"""Parallel multi-client workflow runner.

Runs any workflow (research / process / publish / full / schedule) for
multiple clients simultaneously using a thread pool.  Each client is fully
isolated — separate settings, orchestrator, and log files.

Usage examples
--------------
Run research for all clients in parallel:

    runner = MultiClientRunner()
    results = runner.run_workflow("research")

Run the scheduler for all clients (long-running, blocks until Ctrl+C):

    runner.run_all_schedulers()

Run a single client:

    results = runner.run_workflow("research", client_names=["acme_corp"])
"""

import time
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict

from rich.console import Console
from rich.table import Table

from client_manager import ClientManager
from orchestrator import ContentOrchestrator
from scheduler import WorkflowScheduler
from utils.logger import get_client_logger, log

console = Console()

# Maximum number of clients that will run concurrently.
# Raise this if you have many clients and fast hardware; lower it to reduce
# simultaneous OpenAI / LinkedIn / Trello API calls.
DEFAULT_MAX_WORKERS = 5


class MultiClientRunner:
    """Orchestrates parallel workflow execution across multiple clients."""

    def __init__(self, max_workers: int = DEFAULT_MAX_WORKERS):
        """Initialise the runner.

        Args:
            max_workers: Maximum number of clients to process in parallel.
        """
        self.manager = ClientManager()
        self.max_workers = max_workers
        self._active_schedulers: List[WorkflowScheduler] = []
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # One-shot workflows
    # ------------------------------------------------------------------

    def run_workflow(
        self,
        workflow: str,
        client_names: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Run a workflow for one or more clients in parallel.

        Args:
            workflow: One of 'research', 'process', 'publish', 'full'.
            client_names: Specific clients to target.  If None, all
                          registered clients are used.

        Returns:
            List of result dicts: {client, success, error}
        """
        targets = client_names or self.manager.list_clients()

        if not targets:
            console.print("[yellow]No clients found. Add env files to the clients/ directory.[/yellow]")
            return []

        console.print(
            f"\n[bold cyan]Running '{workflow}' workflow for "
            f"{len(targets)} client(s) with up to {self.max_workers} parallel workers...[/bold cyan]\n"
        )

        results: List[Dict] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(self._run_single, client, workflow): client
                for client in targets
            }
            for future in as_completed(futures):
                client = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"client": client, "success": False, "error": str(exc)}
                results.append(result)

        self._print_results_table(results, workflow)
        return results

    def _run_single(self, client_name: str, workflow: str) -> Dict:
        """Run a workflow for a single client (executes in a worker thread).

        Args:
            client_name: Registered client name.
            workflow: Workflow type.

        Returns:
            Result dict: {client, success, error}
        """
        client_log = get_client_logger(client_name)
        client_log.info(f"Starting '{workflow}' workflow")

        try:
            orchestrator = self.manager.create_orchestrator(client_name)

            dispatch = {
                "research": orchestrator.run_daily_research,
                "process": orchestrator.process_approved_topics,
                "publish": orchestrator.publish_approved_content,
                "full": orchestrator.run_full_workflow,
            }

            if workflow not in dispatch:
                raise ValueError(
                    f"Unknown workflow '{workflow}'. "
                    f"Choose from: {', '.join(dispatch)}"
                )

            dispatch[workflow]()
            client_log.info(f"'{workflow}' workflow completed successfully")
            return {"client": client_name, "success": True, "error": None}

        except Exception as exc:
            client_log.error(f"'{workflow}' workflow failed: {exc}")
            return {"client": client_name, "success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Scheduler mode
    # ------------------------------------------------------------------

    def run_all_schedulers(
        self,
        client_names: Optional[List[str]] = None,
        research_hour: int = 9,
        research_minute: int = 0,
        process_interval_hours: int = 2,
        publish_interval_hours: int = 1,
    ):
        """Start a persistent scheduler for every client.

        All client schedulers run in background threads.  This method blocks
        until a SIGINT (Ctrl+C) or SIGTERM is received, then shuts down all
        schedulers cleanly.

        Args:
            client_names: Clients to schedule. Defaults to all registered.
            research_hour: Hour (0-23) for the daily research cron job.
            research_minute: Minute (0-59) for the daily research cron job.
            process_interval_hours: How often to process approved topics.
            publish_interval_hours: How often to check for content to publish.
        """
        targets = client_names or self.manager.list_clients()

        if not targets:
            console.print("[yellow]No clients found. Nothing to schedule.[/yellow]")
            return

        console.print(
            f"\n[bold cyan]Starting schedulers for {len(targets)} client(s)...[/bold cyan]\n"
        )

        for client_name in targets:
            try:
                scheduler = self.manager.create_scheduler(client_name)
                scheduler.schedule_daily_research(
                    hour=research_hour, minute=research_minute
                )
                scheduler.schedule_process_approvals(
                    interval_hours=process_interval_hours
                )
                scheduler.schedule_publish_content(
                    interval_hours=publish_interval_hours
                )
                scheduler.start()
                self._active_schedulers.append(scheduler)
                console.print(f"  [green]✓[/green] Scheduler started for [cyan]{client_name}[/cyan]")
            except Exception as exc:
                console.print(
                    f"  [red]✗[/red] Failed to start scheduler for [cyan]{client_name}[/cyan]: {exc}"
                )
                log.error(f"Scheduler startup failed for '{client_name}': {exc}")

        if not self._active_schedulers:
            console.print("[bold red]No schedulers could be started. Check client configurations.[/bold red]")
            return

        console.print(
            f"\n[bold green]✓ {len(self._active_schedulers)} scheduler(s) running.[/bold green]"
        )
        console.print("[yellow]Press Ctrl+C to stop all schedulers.[/yellow]\n")

        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Block main thread until stop event is set
        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self._shutdown_all()

    def _handle_shutdown(self, signum, frame):
        """Handle OS shutdown signals."""
        console.print("\n[yellow]Shutdown signal received...[/yellow]")
        self._shutdown_all()

    def _shutdown_all(self):
        """Stop all active schedulers."""
        console.print(f"[yellow]Stopping {len(self._active_schedulers)} scheduler(s)...[/yellow]")
        for scheduler in self._active_schedulers:
            try:
                scheduler.stop()
            except Exception:
                pass
        self._active_schedulers.clear()
        console.print("[bold green]All schedulers stopped. Goodbye![/bold green]\n")
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _print_results_table(self, results: List[Dict], workflow: str):
        """Print a summary table of workflow run results."""
        table = Table(
            title=f"Multi-Client '{workflow}' Workflow Results",
            show_header=True,
        )
        table.add_column("Client", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Error", style="red")

        successes = sum(1 for r in results if r["success"])
        for r in sorted(results, key=lambda x: x["client"]):
            status = "[green]✓ Success[/green]" if r["success"] else "[red]✗ Failed[/red]"
            error = r["error"] or ""
            table.add_row(r["client"], status, error)

        console.print(table)
        console.print(
            f"\n[bold]Summary:[/bold] {successes}/{len(results)} clients completed successfully.\n"
        )

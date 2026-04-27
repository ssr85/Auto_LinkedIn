#!/usr/bin/env python3
"""
Main entry point for the LinkedIn Content Automation System.

Single-client (original) usage is fully preserved:
  python main.py research
  python main.py schedule

Multi-client usage:
  python main.py research  --client acme_corp
  python main.py research  --all-clients
  python main.py schedule  --all-clients
  python main.py clients   list
  python main.py clients   validate
"""

import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# --- Pydantic v2 Late-Binding Fix ---
# This resolves: ChatOpenAI is not fully defined; you should define BaseCache, then call ChatOpenAI.model_rebuild()
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.caches import BaseCache
    from langchain_core.callbacks import Callbacks
    ChatOpenAI.model_rebuild()
except ImportError:
    pass
# ------------------------------------

from orchestrator import ContentOrchestrator
from scheduler import WorkflowScheduler
from client_manager import ClientManager
from multi_client_runner import MultiClientRunner
from utils.logger import log
from utils.telemetry import init_tracing
from config import settings


console = Console()


# ---------------------------------------------------------------------------
# Banner / config display
# ---------------------------------------------------------------------------

def print_banner():
    """Print application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║         LinkedIn Content Automation System                   ║
    ║         Powered by CrewAI & AI Agents                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_config():
    """Print current (default) configuration."""
    table = Table(title="Current Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Target URL", settings.target_url)
    table.add_row("Industry", settings.target_industry)
    table.add_row("AI Model", settings.ai_model)
    table.add_row("Research Frequency", f"{settings.research_frequency_hours} hours")
    table.add_row("Max Topics per Research", str(settings.max_topics_per_research))

    console.print(table)


# ---------------------------------------------------------------------------
# Single-client workflow helpers
# ---------------------------------------------------------------------------

def _make_orchestrator(client_name=None) -> ContentOrchestrator:
    """Return an orchestrator — either default or for a named client."""
    if client_name:
        manager = ClientManager()
        return manager.create_orchestrator(client_name)
    return ContentOrchestrator()


def _make_scheduler(client_name=None) -> WorkflowScheduler:
    """Return a scheduler — either default or for a named client."""
    if client_name:
        manager = ClientManager()
        return manager.create_scheduler(client_name)
    return WorkflowScheduler()


def run_research_workflow(client_name=None):
    """Run the research workflow."""
    console.print("\n[bold cyan]Starting Research Workflow...[/bold cyan]\n")

    orchestrator = _make_orchestrator(client_name)
    # Only prompt for URL/industry in single-client interactive mode
    if not client_name:
        url = console.input(
            f"[bold white]Enter Target URL[/bold white] (default: {settings.target_url}): "
        ).strip() or settings.target_url
        industry = console.input(
            f"[bold white]Enter Target Industry[/bold white] (default: {settings.target_industry}): "
        ).strip() or settings.target_industry
        orchestrator.run_daily_research(url=url, industry=industry)
    else:
        orchestrator.run_daily_research()

    console.print("\n[bold green]✓ Research workflow completed![/bold green]")
    console.print("Check your Trello board for new topic cards.\n")


def run_process_workflow(client_name=None):
    """Run the topic processing workflow."""
    console.print("\n[bold cyan]Processing Approved Topics...[/bold cyan]\n")
    _make_orchestrator(client_name).process_approved_topics()
    console.print("\n[bold green]✓ Topic processing completed![/bold green]")
    console.print("Check your Trello board for new content cards.\n")


def run_publish_workflow(client_name=None):
    """Run the publishing workflow."""
    console.print("\n[bold cyan]Publishing Approved Content...[/bold cyan]\n")
    _make_orchestrator(client_name).publish_approved_content()
    console.print("\n[bold green]✓ Publishing workflow completed![/bold green]")
    console.print("Check LinkedIn for your new posts.\n")


def run_full_workflow(client_name=None):
    """Run the complete workflow."""
    console.print("\n[bold cyan]Running Full Workflow...[/bold cyan]\n")
    _make_orchestrator(client_name).run_full_workflow()
    console.print("\n[bold green]✓ Full workflow completed![/bold green]\n")


def validate_setup(client_name=None):
    """Validate system setup."""
    console.print("\n[bold cyan]Validating System Setup...[/bold cyan]\n")
    orchestrator = _make_orchestrator(client_name)
    if orchestrator.validate_setup():
        console.print("\n[bold green]✓ All systems validated successfully![/bold green]\n")
        return True
    console.print("\n[bold red]✗ System validation failed. Please check your configuration.[/bold red]\n")
    return False


def start_scheduler(client_name=None):
    """Start the automated scheduler for a single client."""
    console.print("\n[bold cyan]Starting Automated Scheduler...[/bold cyan]\n")

    scheduler = _make_scheduler(client_name)

    if not scheduler.orchestrator.validate_setup():
        console.print("[bold red]Setup validation failed. Please fix configuration errors.[/bold red]")
        sys.exit(1)

    scheduler.schedule_daily_research(hour=9, minute=0)
    scheduler.schedule_process_approvals(interval_hours=2)
    scheduler.schedule_publish_content(interval_hours=1)
    scheduler.start()

    console.print("\n[bold green]✓ Scheduler started successfully![/bold green]")
    console.print("\nScheduled jobs:")
    scheduler.print_schedule()
    console.print("\n[yellow]Press Ctrl+C to stop the scheduler[/yellow]\n")

    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        scheduler.stop()
        console.print("[bold green]Goodbye![/bold green]\n")


# ---------------------------------------------------------------------------
# Multi-client helpers
# ---------------------------------------------------------------------------

def run_all_clients_workflow(workflow: str):
    """Run a one-shot workflow for every registered client in parallel."""
    runner = MultiClientRunner()
    runner.run_workflow(workflow)


def start_all_schedulers():
    """Start persistent schedulers for every registered client."""
    runner = MultiClientRunner()
    runner.run_all_schedulers()


# ---------------------------------------------------------------------------
# clients sub-command
# ---------------------------------------------------------------------------

def cmd_clients(sub: str):
    """Handle `clients list` and `clients validate` sub-commands."""
    manager = ClientManager()
    if sub == "list":
        manager.print_client_table()
    elif sub == "validate":
        console.print("\n[bold cyan]Validating all registered clients...[/bold cyan]\n")
        results = manager.validate_all_clients()
        manager.print_validation_table(results)
    else:
        console.print(f"[red]Unknown clients sub-command '{sub}'. Use: list, validate[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Main CLI entry point."""
    # Initialize OpenTelemetry tracing (Console output)
    init_tracing()
    
    parser = argparse.ArgumentParser(
        description="LinkedIn Content Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Single-client examples (uses .env):
  %(prog)s research              Run research workflow
  %(prog)s process               Process approved topics
  %(prog)s publish               Publish approved content
  %(prog)s full                  Run complete workflow
  %(prog)s schedule              Start automated scheduler
  %(prog)s validate              Validate system setup
  %(prog)s config                Show current configuration

Per-client examples (uses clients/<name>.env):
  %(prog)s research  --client acme_corp
  %(prog)s schedule  --client acme_corp

All-client parallel examples:
  %(prog)s research  --all-clients
  %(prog)s process   --all-clients
  %(prog)s publish   --all-clients
  %(prog)s full      --all-clients
  %(prog)s schedule  --all-clients

Client management:
  %(prog)s clients list          List all registered clients
  %(prog)s clients validate      Validate all client configurations
        """
    )

    parser.add_argument(
        'command',
        choices=['research', 'process', 'publish', 'full', 'schedule',
                 'validate', 'config', 'clients'],
        help='Command to execute'
    )

    parser.add_argument(
        'subcommand',
        nargs='?',
        help="Sub-command for 'clients' (list | validate)"
    )

    parser.add_argument(
        '--client',
        metavar='NAME',
        default=None,
        help='Run for a specific client (must exist in clients/<NAME>.env)'
    )

    parser.add_argument(
        '--all-clients',
        action='store_true',
        help='Run for all registered clients in parallel'
    )

    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Suppress banner display'
    )

    args = parser.parse_args()

    if not args.no_banner:
        print_banner()

    # Mutual exclusion: --client and --all-clients cannot be combined
    if args.client and args.all_clients:
        console.print("[bold red]Error: --client and --all-clients are mutually exclusive.[/bold red]")
        sys.exit(1)

    try:
        # ---- clients sub-command ----------------------------------------
        if args.command == 'clients':
            sub = args.subcommand or 'list'
            cmd_clients(sub)
            return

        # ---- config (no client targeting) --------------------------------
        if args.command == 'config':
            print_config()
            return

        # ---- all-clients parallel mode -----------------------------------
        if args.all_clients:
            if args.command == 'schedule':
                start_all_schedulers()
            else:
                run_all_clients_workflow(args.command)
            return

        # ---- single-client or default mode -------------------------------
        client = args.client  # may be None (uses .env default)

        dispatch = {
            'research': lambda: run_research_workflow(client),
            'process':  lambda: run_process_workflow(client),
            'publish':  lambda: run_publish_workflow(client),
            'full':     lambda: run_full_workflow(client),
            'schedule': lambda: start_scheduler(client),
            'validate': lambda: validate_setup(client),
        }

        dispatch[args.command]()

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        log.error(f"Command '{args.command}' failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

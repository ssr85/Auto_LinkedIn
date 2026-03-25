"""Client management for multi-client LinkedIn automation.

Clients are defined by env files in the clients/ directory.
Each file named <client_name>.env represents one managed LinkedIn account.

Usage:
    manager = ClientManager()
    manager.list_clients()           -> ['acme_corp', 'techstart']
    manager.load_settings('acme_corp')
    manager.create_orchestrator('acme_corp')
    manager.print_status_table()
"""

import os
import glob
from typing import List, Optional, Dict
from rich.console import Console
from rich.table import Table

from config import load_client_settings, Settings
from orchestrator import ContentOrchestrator
from scheduler import WorkflowScheduler
from utils.logger import get_client_logger

console = Console()

CLIENTS_DIR = "clients"


class ClientManager:
    """Discovers and manages per-client configurations."""

    def __init__(self, clients_dir: str = CLIENTS_DIR):
        self.clients_dir = clients_dir
        os.makedirs(self.clients_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_clients(self) -> List[str]:
        """Return sorted list of registered client names (from *.env files).

        Returns:
            List of client names (filename without .env extension).
        """
        pattern = os.path.join(self.clients_dir, "*.env")
        env_files = glob.glob(pattern)
        clients = sorted(
            os.path.splitext(os.path.basename(f))[0]
            for f in env_files
            if not os.path.basename(f).startswith("example")
        )
        return clients

    def client_env_path(self, client_name: str) -> str:
        """Return the path to a client's env file."""
        return os.path.join(self.clients_dir, f"{client_name}.env")

    def client_exists(self, client_name: str) -> bool:
        """Check whether a client env file exists."""
        return os.path.isfile(self.client_env_path(client_name))

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_settings(self, client_name: str) -> Settings:
        """Load and return a Settings instance for the given client.

        Args:
            client_name: Name matching a file in clients/<name>.env

        Returns:
            Validated Settings object for that client.

        Raises:
            FileNotFoundError: If the env file does not exist.
            ValueError: If settings validation fails.
        """
        env_path = self.client_env_path(client_name)
        if not os.path.isfile(env_path):
            raise FileNotFoundError(
                f"Client '{client_name}' not found. "
                f"Expected env file at: {env_path}"
            )
        return load_client_settings(env_file=env_path, client_name=client_name)

    def create_orchestrator(self, client_name: str) -> ContentOrchestrator:
        """Create and return a ContentOrchestrator for the given client.

        Args:
            client_name: Registered client name.

        Returns:
            ContentOrchestrator initialised with that client's settings.
        """
        client_settings = self.load_settings(client_name)
        return ContentOrchestrator(settings=client_settings)

    def create_scheduler(self, client_name: str) -> WorkflowScheduler:
        """Create and return a WorkflowScheduler for the given client.

        Args:
            client_name: Registered client name.

        Returns:
            WorkflowScheduler initialised with that client's settings.
        """
        client_settings = self.load_settings(client_name)
        return WorkflowScheduler(settings=client_settings)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_client(self, client_name: str) -> Dict:
        """Validate a single client's configuration and integrations.

        Args:
            client_name: Registered client name.

        Returns:
            Dict with keys: client, settings_ok, integrations_ok, error
        """
        result: Dict = {
            "client": client_name,
            "settings_ok": False,
            "integrations_ok": False,
            "error": None,
        }
        try:
            orchestrator = self.create_orchestrator(client_name)
            result["settings_ok"] = True
            result["integrations_ok"] = orchestrator.validate_setup()
        except Exception as exc:
            result["error"] = str(exc)
        return result

    def validate_all_clients(self) -> List[Dict]:
        """Validate every registered client.

        Returns:
            List of validation result dicts (one per client).
        """
        clients = self.list_clients()
        if not clients:
            console.print("[yellow]No clients registered. Add env files to clients/ directory.[/yellow]")
            return []
        return [self.validate_client(c) for c in clients]

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def print_client_table(self):
        """Print a Rich table listing all registered clients."""
        clients = self.list_clients()

        table = Table(title="Registered Clients", show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Client Name", style="cyan")
        table.add_column("Env File", style="dim")
        table.add_column("Exists", style="green")

        if not clients:
            console.print("[yellow]No clients registered.[/yellow]")
            console.print(f"Add <client_name>.env files to the [cyan]{self.clients_dir}/[/cyan] directory.")
            return

        for i, client in enumerate(clients, 1):
            path = self.client_env_path(client)
            exists = "[green]✓[/green]" if os.path.isfile(path) else "[red]✗[/red]"
            table.add_row(str(i), client, path, exists)

        console.print(table)

    def print_validation_table(self, results: Optional[List[Dict]] = None):
        """Print a Rich table with validation results for all clients.

        Args:
            results: Pre-computed validation results. If None, runs validation.
        """
        if results is None:
            results = self.validate_all_clients()

        table = Table(title="Client Validation Results", show_header=True)
        table.add_column("Client", style="cyan")
        table.add_column("Settings", justify="center")
        table.add_column("Integrations", justify="center")
        table.add_column("Error", style="red")

        for r in results:
            settings_icon = "[green]✓[/green]" if r["settings_ok"] else "[red]✗[/red]"
            integrations_icon = "[green]✓[/green]" if r["integrations_ok"] else "[red]✗[/red]"
            error_text = r["error"] or ""
            table.add_row(r["client"], settings_icon, integrations_icon, error_text)

        console.print(table)

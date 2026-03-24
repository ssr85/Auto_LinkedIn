#!/usr/bin/env python3
"""
Custom script to run the full workflow with specific URL and industry.
"""

from orchestrator import ContentOrchestrator
from rich.console import Console
from utils.logger import log

console = Console()

def main():
    """Run full workflow with custom parameters."""
    # Custom parameters
    url = "www.oghemp.in/deckle2"
    industry = "Deckle edge papers"

    # Ensure URL has proper protocol
    if not url.startswith("http"):
        url = f"https://{url}"

    console.print("\n[bold cyan]Starting Full Workflow with Custom Parameters[/bold cyan]\n")
    console.print(f"[yellow]URL:[/yellow] {url}")
    console.print(f"[yellow]Industry:[/yellow] {industry}\n")

    # Initialize and run
    orchestrator = ContentOrchestrator()
    orchestrator.run_full_workflow(url=url, industry=industry)

    console.print("\n[bold green]✓ Custom workflow completed![/bold green]\n")

if __name__ == "__main__":
    main()

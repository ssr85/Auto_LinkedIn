#!/usr/bin/env python3
"""
Script to check the results of the workflow on Trello.
"""

from integrations.trello_client import TrelloManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def main():
    """Check and display Trello cards created."""
    console.print("\n[bold cyan]Checking Trello Board for Results...[/bold cyan]\n")

    trello = TrelloManager()

    # Get all cards from the topics list
    console.print("[yellow]Fetching topic cards from Trello...[/yellow]\n")

    try:
        topics_cards = trello.topics_list.list_cards()

        if topics_cards:
            table = Table(title="📋 Topic Cards Created", show_header=True, header_style="bold magenta")
            table.add_column("#", style="cyan", width=3)
            table.add_column("Card Name", style="green", width=60)
            table.add_column("Card ID", style="yellow", width=25)

            for idx, card in enumerate(topics_cards, 1):
                table.add_row(str(idx), card.name, card.id)

            console.print(table)
            console.print(f"\n[bold green]✓ Total cards created: {len(topics_cards)}[/bold green]\n")

            # Show details of first card as example
            if topics_cards:
                first_card = topics_cards[0]
                panel = Panel(
                    f"[bold]Card Name:[/bold] {first_card.name}\n\n"
                    f"[bold]URL:[/bold] {first_card.url}\n\n"
                    f"[bold]Description Preview:[/bold]\n{first_card.desc[:300]}...",
                    title="📄 First Card Preview",
                    border_style="blue"
                )
                console.print(panel)

                console.print(f"\n[cyan]View all cards on Trello:[/cyan] {trello.board.url}\n")
        else:
            console.print("[yellow]No topic cards found.[/yellow]\n")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]\n")

if __name__ == "__main__":
    main()

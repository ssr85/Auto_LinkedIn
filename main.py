#!/usr/bin/env python3
"""
Main entry point for the LinkedIn Content Automation System.

This script provides a CLI interface for running different workflows.
"""

import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orchestrator import ContentOrchestrator
from scheduler import WorkflowScheduler
from utils.logger import log
from config import settings


console = Console()


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
    """Print current configuration."""
    table = Table(title="Current Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Target URL", settings.target_url)
    table.add_row("Industry", settings.target_industry)
    table.add_row("AI Model", settings.ai_model)
    table.add_row("Research Frequency", f"{settings.research_frequency_hours} hours")
    table.add_row("Max Topics per Research", str(settings.max_topics_per_research))

    console.print(table)


def run_research_workflow():
    """Run the research workflow."""
    console.print("\n[bold cyan]Starting Research Workflow...[/bold cyan]\n")

    # Interactive input for URL and Industry
    url = console.input(f"[bold white]Enter Target URL[/bold white] (default: {settings.target_url}): ").strip()
    industry = console.input(f"[bold white]Enter Target Industry[/bold white] (default: {settings.target_industry}): ").strip()

    # Fall back to defaults if empty
    url = url if url else settings.target_url
    industry = industry if industry else settings.target_industry

    orchestrator = ContentOrchestrator()
    orchestrator.run_daily_research(url=url, industry=industry)

    console.print("\n[bold green]✓ Research workflow completed![/bold green]")
    console.print("Check your Trello board for new topic cards.\n")


def run_process_workflow():
    """Run the topic processing workflow."""
    console.print("\n[bold cyan]Processing Approved Topics...[/bold cyan]\n")

    orchestrator = ContentOrchestrator()
    orchestrator.process_approved_topics()

    console.print("\n[bold green]✓ Topic processing completed![/bold green]")
    console.print("Check your Trello board for new content cards.\n")


def run_publish_workflow():
    """Run the publishing workflow."""
    console.print("\n[bold cyan]Publishing Approved Content...[/bold cyan]\n")

    orchestrator = ContentOrchestrator()
    orchestrator.publish_approved_content()

    console.print("\n[bold green]✓ Publishing workflow completed![/bold green]")
    console.print("Check LinkedIn for your new posts.\n")


def run_full_workflow():
    """Run the complete workflow."""
    console.print("\n[bold cyan]Running Full Workflow...[/bold cyan]\n")

    orchestrator = ContentOrchestrator()
    orchestrator.run_full_workflow()

    console.print("\n[bold green]✓ Full workflow completed![/bold green]\n")


def validate_setup():
    """Validate system setup."""
    console.print("\n[bold cyan]Validating System Setup...[/bold cyan]\n")

    orchestrator = ContentOrchestrator()
    if orchestrator.validate_setup():
        console.print("\n[bold green]✓ All systems validated successfully![/bold green]\n")
        return True
    else:
        console.print("\n[bold red]✗ System validation failed. Please check your configuration.[/bold red]\n")
        return False


def start_scheduler():
    """Start the automated scheduler."""
    console.print("\n[bold cyan]Starting Automated Scheduler...[/bold cyan]\n")

    scheduler = WorkflowScheduler()

    # Validate first
    if not scheduler.orchestrator.validate_setup():
        console.print("[bold red]Setup validation failed. Please fix configuration errors.[/bold red]")
        sys.exit(1)

    # Schedule workflows
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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Content Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s research              Run research workflow
  %(prog)s process               Process approved topics
  %(prog)s publish               Publish approved content
  %(prog)s full                  Run complete workflow
  %(prog)s schedule              Start automated scheduler
  %(prog)s validate              Validate system setup
  %(prog)s config                Show current configuration
        """
    )

    parser.add_argument(
        'command',
        choices=['research', 'process', 'publish', 'full', 'schedule', 'validate', 'config'],
        help='Command to execute'
    )

    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Suppress banner display'
    )

    args = parser.parse_args()

    # Print banner
    if not args.no_banner:
        print_banner()

    # Execute command
    commands = {
        'research': run_research_workflow,
        'process': run_process_workflow,
        'publish': run_publish_workflow,
        'full': run_full_workflow,
        'schedule': start_scheduler,
        'validate': validate_setup,
        'config': print_config
    }

    try:
        commands[args.command]()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        log.error(f"Command '{args.command}' failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

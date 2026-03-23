"""Scheduler for automating the content workflow at specified intervals."""

import schedule
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from orchestrator import ContentOrchestrator
from utils.logger import log
from config import settings


class WorkflowScheduler:
    """Manages scheduled execution of the content workflow."""

    def __init__(self):
        """Initialize the scheduler."""
        self.orchestrator = ContentOrchestrator()
        self.scheduler = BackgroundScheduler()

    def schedule_daily_research(self, hour: int = 9, minute: int = 0):
        """
        Schedule daily research to run at specified time.

        Args:
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        log.info(f"Scheduling daily research for {hour:02d}:{minute:02d}")

        self.scheduler.add_job(
            self.orchestrator.run_daily_research,
            CronTrigger(hour=hour, minute=minute),
            id='daily_research',
            name='Daily Research Workflow',
            replace_existing=True
        )

    def schedule_process_approvals(self, interval_hours: int = 2):
        """
        Schedule periodic checking and processing of approved topics.

        Args:
            interval_hours: Check interval in hours
        """
        log.info(f"Scheduling approval processing every {interval_hours} hours")

        self.scheduler.add_job(
            self.orchestrator.process_approved_topics,
            'interval',
            hours=interval_hours,
            id='process_approvals',
            name='Process Approved Topics',
            replace_existing=True
        )

    def schedule_publish_content(self, interval_hours: int = 1):
        """
        Schedule periodic checking and publishing of approved content.

        Args:
            interval_hours: Check interval in hours
        """
        log.info(f"Scheduling content publishing every {interval_hours} hours")

        self.scheduler.add_job(
            self.orchestrator.publish_approved_content,
            'interval',
            hours=interval_hours,
            id='publish_content',
            name='Publish Approved Content',
            replace_existing=True
        )

    def schedule_full_workflow(self, cron_expression: str = "0 9 * * *"):
        """
        Schedule the complete workflow using a cron expression.

        Args:
            cron_expression: Cron expression (default: 9 AM daily)
                            Format: minute hour day month day_of_week
        """
        log.info(f"Scheduling full workflow with cron: {cron_expression}")

        parts = cron_expression.split()
        if len(parts) != 5:
            log.error("Invalid cron expression. Using default: 0 9 * * *")
            parts = ["0", "9", "*", "*", "*"]

        self.scheduler.add_job(
            self.orchestrator.run_full_workflow,
            CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4]
            ),
            id='full_workflow',
            name='Full Content Workflow',
            replace_existing=True
        )

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            log.info("Starting scheduler...")
            self.scheduler.start()
            log.info("Scheduler started successfully")

            # Print scheduled jobs
            self.print_schedule()
        else:
            log.warning("Scheduler is already running")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            log.info("Stopping scheduler...")
            self.scheduler.shutdown()
            log.info("Scheduler stopped")
        else:
            log.warning("Scheduler is not running")

    def print_schedule(self):
        """Print all scheduled jobs."""
        log.info("\n" + "=" * 70)
        log.info("SCHEDULED JOBS")
        log.info("=" * 70)

        jobs = self.scheduler.get_jobs()

        if not jobs:
            log.info("No jobs scheduled")
        else:
            for job in jobs:
                log.info(f"\nJob: {job.name}")
                log.info(f"  ID: {job.id}")
                log.info(f"  Next run: {job.next_run_time}")
                log.info(f"  Trigger: {job.trigger}")

        log.info("=" * 70 + "\n")

    def run_immediately(self, workflow_type: str = "full"):
        """
        Run a workflow immediately (for testing).

        Args:
            workflow_type: Type of workflow to run
                          ('research', 'process', 'publish', 'full')
        """
        log.info(f"Running {workflow_type} workflow immediately...")

        workflows = {
            'research': self.orchestrator.run_daily_research,
            'process': self.orchestrator.process_approved_topics,
            'publish': self.orchestrator.publish_approved_content,
            'full': self.orchestrator.run_full_workflow
        }

        if workflow_type in workflows:
            workflows[workflow_type]()
        else:
            log.error(f"Unknown workflow type: {workflow_type}")
            log.info(f"Available types: {', '.join(workflows.keys())}")


def main():
    """Main entry point for the scheduler."""
    log.info("\n" + "=" * 70)
    log.info("LINKEDIN CONTENT AUTOMATION SCHEDULER")
    log.info("=" * 70 + "\n")

    # Create scheduler instance
    scheduler = WorkflowScheduler()

    # Validate setup before scheduling
    log.info("Validating system setup...")
    if not scheduler.orchestrator.validate_setup():
        log.error("Setup validation failed. Please fix configuration errors.")
        return

    log.info("✓ System validation passed\n")

    # Schedule workflows
    try:
        # Daily research at 9 AM
        scheduler.schedule_daily_research(hour=9, minute=0)

        # Check for approved topics every 2 hours
        scheduler.schedule_process_approvals(interval_hours=2)

        # Check for approved content to publish every hour
        scheduler.schedule_publish_content(interval_hours=1)

        # Start the scheduler
        scheduler.start()

        log.info("Scheduler is running. Press Ctrl+C to stop.\n")

        # Keep the script running
        try:
            while True:
                time.sleep(60)  # Sleep for 1 minute
        except KeyboardInterrupt:
            log.info("\nReceived shutdown signal...")
            scheduler.stop()
            log.info("Scheduler stopped. Goodbye!")

    except Exception as e:
        log.error(f"Scheduler error: {str(e)}")
        scheduler.stop()


if __name__ == "__main__":
    main()

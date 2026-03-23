"""Main orchestration script for the LinkedIn content automation system."""

from typing import List, Dict, Optional
from datetime import datetime
import time

from agents.research_agent import ResearchAgent
from agents.content_agent import ContentAgent
from integrations.trello_client import TrelloManager
from integrations.linkedin_client import LinkedInManager
from utils.logger import log
from config import settings


class ContentOrchestrator:
    """Orchestrates the entire content creation and publishing workflow."""

    def __init__(self):
        """Initialize the orchestrator with all required components."""
        log.info("Initializing Content Orchestrator")

        self.research_agent = ResearchAgent()
        self.content_agent = ContentAgent()
        self.trello = TrelloManager()
        self.linkedin = LinkedInManager()

    def run_daily_research(self, url: Optional[str] = None, industry: Optional[str] = None):
        """
        Execute research workflow:
        1. Research topics based on URL and industry
        2. Create Trello cards for approval
        """
        # Use provided values or fall back to settings
        target_url = url or settings.target_url
        target_industry = industry or settings.target_industry

        log.info("=" * 70)
        log.info("STARTING RESEARCH WORKFLOW")
        log.info("=" * 70)

        try:
            # Step 1: Research topics
            log.info(f"Researching topics for {target_industry} industry")
            log.info(f"Source URL: {target_url}")

            topics = self.research_agent.research_topics(
                url=target_url,
                industry=target_industry,
                num_topics=settings.max_topics_per_research
            )

            if not topics:
                log.warning("No topics generated from research")
                return

            log.info(f"Research completed. Generated {len(topics)} topics")

            # Step 2: Create Trello cards for each topic
            log.info("Creating Trello cards for approval")

            for topic in topics:
                if not self.research_agent.validate_topic(topic):
                    log.warning(f"Skipping invalid topic: {topic.get('title', 'Unknown')}")
                    continue

                try:
                    card_id = self.trello.create_topic_card(
                        topic=topic['title'],
                        outline=topic['outline'],
                        metadata=topic['metadata']
                    )

                    log.info(f"✓ Created card for topic: {topic['title']}")

                except Exception as e:
                    log.error(f"Failed to create card for topic '{topic['title']}': {str(e)}")

            log.info("=" * 70)
            log.info("DAILY RESEARCH WORKFLOW COMPLETED")
            log.info(f"Created {len(topics)} topic cards for approval")
            log.info("=" * 70)

        except Exception as e:
            log.error(f"Daily research workflow failed: {str(e)}")

    def process_approved_topics(self):
        """
        Process approved topics:
        1. Get approved topics from Trello
        2. Generate content for each
        3. Create Trello cards for content approval
        """
        log.info("=" * 70)
        log.info("PROCESSING APPROVED TOPICS")
        log.info("=" * 70)

        try:
            # Step 1: Get approved topics
            approved_topics = self.trello.get_approved_topics()

            if not approved_topics:
                log.info("No approved topics found")
                return

            log.info(f"Found {len(approved_topics)} approved topics")

            # Step 2: Generate content for each topic
            for topic in approved_topics:
                try:
                    log.info(f"Generating content for: {topic['title']}")

                    # Parse topic data from Trello card
                    topic_data = self._parse_trello_topic(topic)

                    # Generate content
                    content_result = self.content_agent.generate_content(topic_data)

                    if not content_result:
                        log.warning(f"Failed to generate content for: {topic['title']}")
                        self.trello.add_comment(
                            topic['id'],
                            "⚠️ Content generation failed. Please review and try again."
                        )
                        continue

                    # Preview content
                    preview = self.content_agent.format_preview(content_result)
                    log.info(f"\n{preview}\n")

                    # Create content approval card
                    content_card_id = self.trello.create_content_card(
                        topic=content_result['topic'],
                        content=content_result['content'],
                        metadata=content_result['metadata']
                    )

                    log.info(f"✓ Created content card for: {topic['title']}")

                    # Add comment to original topic card
                    self.trello.add_comment(
                        topic['id'],
                        f"✓ Content generated and sent for approval. Card ID: {content_card_id}"
                    )

                    # Archive the topic card
                    self.trello.archive_card(topic['id'])

                except Exception as e:
                    log.error(f"Failed to process topic '{topic['title']}': {str(e)}")

            log.info("=" * 70)
            log.info("APPROVED TOPICS PROCESSING COMPLETED")
            log.info("=" * 70)

        except Exception as e:
            log.error(f"Failed to process approved topics: {str(e)}")

    def publish_approved_content(self):
        """
        Publish approved content with a 60-second grace period:
        1. Get approved content from Trello
        2. Filter by due date
        3. Wait 60 seconds (grace period)
        4. Re-verify the card is still in the approved list
        5. Post to LinkedIn
        """
        log.info("=" * 70)
        log.info("PUBLISHING APPROVED CONTENT")
        log.info("=" * 70)

        try:
            # Step 1: Get approved content
            approved_content = self.trello.get_approved_content()

            if not approved_content:
                log.info("No approved content found")
                return

            log.info(f"Found {len(approved_content)} approved content items")

            # Step 2: Post each to LinkedIn
            for content_item in approved_content:
                try:
                    # Check if scheduled for future
                    now = datetime.now() # Naive or local, since we'll use it for the grace period check
                    due_date = content_item.get('due_date')
                    if due_date:
                        # Ensure we compare in the same timezone (Trello uses UTC)
                        now_tz = datetime.now(due_date.tzinfo) if due_date.tzinfo else datetime.now()
                        if due_date > now_tz:
                            log.info(f"Skipping '{content_item['title']}' - scheduled for {due_date.strftime('%Y-%m-%d %H:%M')}")
                            continue

                    # Grace period (60 seconds)
                    log.info(f"⏳ Grace Period: Posting '{content_item['title']}' in 60 seconds...")
                    log.info("   (Move the card out of 'Approved Content' to cancel)")
                    time.sleep(60)

                    # RE-VERIFY: Check if the card is still in the 'Approved Content' list
                    # Get fresh list of approved content
                    current_approved = self.trello.get_approved_content()
                    is_still_approved = any(item['id'] == content_item['id'] for item in current_approved)

                    if not is_still_approved:
                        log.info(f"🚫 Posting cancelled for '{content_item['title']}' (card was moved/removed)")
                        continue

                    log.info(f"🚀 Grace period over. Publishing: {content_item['title']}")

                    # Preview before posting
                    preview = self.linkedin.preview_post(
                        content=content_item['content']
                    )
                    log.info(f"\n{preview}\n")

                    # Post to LinkedIn
                    result = self.linkedin.post_content(
                        content=content_item['content']
                    )

                    if result['success']:
                        log.info(f"✓ Successfully posted to LinkedIn. Post ID: {result['post_id']}")

                        # Add comment to Trello card
                        self.trello.add_comment(
                            content_item['id'],
                            f"✓ Published to LinkedIn\nPost ID: {result['post_id']}\nPublished at: {datetime.now().isoformat()}"
                        )

                        # Archive the card
                        self.trello.archive_card(content_item['id'])

                    else:
                        log.error(f"Failed to post to LinkedIn: {result.get('error', 'Unknown error')}")

                        # Add error comment to Trello
                        self.trello.add_comment(
                            content_item['id'],
                            f"⚠️ Failed to publish to LinkedIn\nError: {result.get('error', 'Unknown error')}"
                        )

                    # Rate limiting - wait between posts
                    time.sleep(5)

                except Exception as e:
                    log.error(f"Failed to publish content '{content_item['title']}': {str(e)}")

            log.info("=" * 70)
            log.info("CONTENT PUBLISHING COMPLETED")
            log.info("=" * 70)

        except Exception as e:
            log.error(f"Failed to publish approved content: {str(e)}")

    def run_full_workflow(self):
        """
        Run the complete workflow:
        1. Daily research
        2. Process approved topics
        3. Publish approved content
        """
        log.info("\n" + "=" * 70)
        log.info("STARTING FULL WORKFLOW")
        log.info("=" * 70 + "\n")

        try:
            # Step 1: Daily research
            self.run_daily_research()
            time.sleep(2)

            # Step 2: Process approved topics (if any)
            self.process_approved_topics()
            time.sleep(2)

            # Step 3: Publish approved content (if any)
            self.publish_approved_content()

            log.info("\n" + "=" * 70)
            log.info("FULL WORKFLOW COMPLETED SUCCESSFULLY")
            log.info("=" * 70 + "\n")

        except Exception as e:
            log.error(f"Full workflow failed: {str(e)}")

    def _parse_trello_topic(self, trello_card: Dict) -> Dict:
        """
        Parse topic data from Trello card format.

        Args:
            trello_card: Trello card dictionary

        Returns:
            Topic dictionary for content generation
        """
        return {
            'title': trello_card['title'],
            'outline': trello_card['description'],
            'metadata': {
                'source': 'trello',
                'card_id': trello_card['id'],
                'card_url': trello_card.get('url', '')
            }
        }

    def validate_setup(self) -> bool:
        """
        Validate that all integrations are properly configured.

        Returns:
            True if all validations pass, False otherwise
        """
        log.info("Validating system setup...")

        all_valid = True

        # Validate LinkedIn
        try:
            if not self.linkedin.validate_token():
                log.error("LinkedIn token validation failed")
                all_valid = False
            else:
                log.info("✓ LinkedIn integration validated")
        except Exception as e:
            log.error(f"LinkedIn validation error: {str(e)}")
            all_valid = False

        # Validate Trello (basic check)
        try:
            # Try to get lists
            self.trello.topics_list
            self.trello.content_list
            log.info("✓ Trello integration validated")
        except Exception as e:
            log.error(f"Trello validation error: {str(e)}")
            all_valid = False

        if all_valid:
            log.info("✓ All systems validated successfully")
        else:
            log.error("✗ System validation failed. Please check configuration.")

        return all_valid

"""Trello integration for managing topic and content approval workflows."""

from typing import List, Dict, Optional
from trello import TrelloClient
from config import settings
from utils.logger import log


class TrelloManager:
    """Manages Trello board interactions for approval workflows."""

    def __init__(self):
        """Initialize Trello client."""
        self.client = TrelloClient(
            api_key=settings.trello_api_key,
            token=settings.trello_token
        )
        self.board = self.client.get_board(settings.trello_board_id)
        self.topics_list = self.client.get_list(settings.trello_topics_list_id)
        self.content_list = self.client.get_list(settings.trello_content_list_id)

    def create_topic_card(self, topic: str, outline: str, metadata: Dict) -> str:
        """
        Create a card for topic approval.

        Args:
            topic: The topic title
            outline: The content outline
            metadata: Additional metadata (source, industry, etc.)

        Returns:
            Card ID
        """
        try:
            description = f"""## Topic Outline

{outline}

---

### Metadata
- **Industry**: {metadata.get('industry', 'N/A')}
- **Source URL**: {metadata.get('source_url', 'N/A')}
- **Research Date**: {metadata.get('research_date', 'N/A')}
- **Keywords**: {', '.join(metadata.get('keywords', []))}

---

**Instructions**:
- Move to "Approved" to generate content
- Move to "Rejected" to discard
- Add comments for modifications
"""

            card = self.topics_list.add_card(
                name=f"📝 Topic: {topic}",
                desc=description
            )

            # Add labels for tracking
            self._add_label(card, metadata.get('industry', 'General'), 'blue')

            log.info(f"Created topic card: {topic} (ID: {card.id})")
            return card.id

        except Exception as e:
            log.error(f"Failed to create topic card: {str(e)}")
            raise

    def create_content_card(self, topic: str, content: str, metadata: Dict) -> str:
        """
        Create a card for content approval before LinkedIn posting.

        Args:
            topic: The topic title
            content: The generated content
            metadata: Additional metadata

        Returns:
            Card ID
        """
        try:
            description = f"""## Generated Content

{content}

---

### Metadata
- **Topic**: {topic}
- **Word Count**: {metadata.get('word_count', 0)}
- **Generated Date**: {metadata.get('generated_date', 'N/A')}
- **Target Industry**: {metadata.get('industry', 'N/A')}

---

**Instructions**:
- Move to "Approved" to post on LinkedIn
- Move to "Needs Revision" for modifications
- Move to "Rejected" to discard
"""

            card = self.content_list.add_card(
                name=f"📄 Content: {topic[:50]}...",
                desc=description
            )

            # Add labels
            self._add_label(card, 'Pending Review', 'yellow')

            log.info(f"Created content card: {topic} (ID: {card.id})")
            return card.id

        except Exception as e:
            log.error(f"Failed to create content card: {str(e)}")
            raise

    def get_approved_topics(self) -> List[Dict]:
        """
        Get all approved topics from Trello.

        Returns:
            List of approved topic dictionaries
        """
        try:
            approved_list = self._get_list_by_name("Approved Topics")
            if not approved_list:
                log.warning("'Approved Topics' list not found")
                return []

            approved_cards = approved_list.list_cards()
            topics = []

            for card in approved_cards:
                topics.append({
                    'id': card.id,
                    'title': card.name.replace('📝 Topic: ', ''),
                    'description': card.desc,
                    'url': card.url
                })

            log.info(f"Found {len(topics)} approved topics")
            return topics

        except Exception as e:
            log.error(f"Failed to get approved topics: {str(e)}")
            return []

    def get_approved_content(self) -> List[Dict]:
        """
        Get all approved content ready for LinkedIn posting.

        Returns:
            List of approved content dictionaries
        """
        try:
            approved_list = self._get_list_by_name("Approved Content")
            if not approved_list:
                log.warning("'Approved Content' list not found")
                return []

            approved_cards = approved_list.list_cards()
            content_items = []

            for card in approved_cards:
                # Parse content from description
                content = self._extract_content_from_card(card)
                if content:
                    content_items.append({
                        'id': card.id,
                        'title': card.name.replace('📄 Content: ', ''),
                        'content': content,
                        'url': card.url
                    })

            log.info(f"Found {len(content_items)} approved content items")
            return content_items

        except Exception as e:
            log.error(f"Failed to get approved content: {str(e)}")
            return []

    def archive_card(self, card_id: str) -> bool:
        """
        Archive a card after processing.

        Args:
            card_id: The card ID to archive

        Returns:
            Success status
        """
        try:
            card = self.client.get_card(card_id)
            card.set_closed(True)
            log.info(f"Archived card: {card_id}")
            return True

        except Exception as e:
            log.error(f"Failed to archive card {card_id}: {str(e)}")
            return False

    def add_comment(self, card_id: str, comment: str) -> bool:
        """
        Add a comment to a card.

        Args:
            card_id: The card ID
            comment: The comment text

        Returns:
            Success status
        """
        try:
            card = self.client.get_card(card_id)
            card.comment(comment)
            log.info(f"Added comment to card: {card_id}")
            return True

        except Exception as e:
            log.error(f"Failed to add comment to card {card_id}: {str(e)}")
            return False

    def _get_list_by_name(self, list_name: str):
        """Get a Trello list by name."""
        lists = self.board.list_lists()
        for lst in lists:
            if lst.name == list_name:
                return lst
        return None

    def _add_label(self, card, label_name: str, color: str):
        """Add a label to a card."""
        try:
            # Get or create label
            labels = self.board.get_labels()
            label = next((l for l in labels if l.name == label_name), None)

            if not label:
                label = self.board.add_label(label_name, color)

            card.add_label(label)

        except Exception as e:
            log.warning(f"Failed to add label '{label_name}': {str(e)}")

    def _extract_content_from_card(self, card) -> Optional[str]:
        """Extract content from card description."""
        try:
            desc = card.desc
            # Extract content between "## Generated Content" and "---"
            if "## Generated Content" in desc:
                content_section = desc.split("## Generated Content")[1]
                content = content_section.split("---")[0].strip()
                return content
            return None

        except Exception as e:
            log.error(f"Failed to extract content from card: {str(e)}")
            return None

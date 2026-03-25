"""Content generation agent for creating LinkedIn posts."""

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import Dict, Optional, TYPE_CHECKING
from datetime import datetime
from utils.logger import log
from config import settings as default_settings

if TYPE_CHECKING:
    from config import Settings


class ContentAgent:
    """Agent responsible for generating LinkedIn content from approved topics."""

    def __init__(self, settings: Optional["Settings"] = None):
        """Initialize the content generation agent.

        Args:
            settings: Settings instance to use. Defaults to global settings.
        """
        self.settings = settings or default_settings
        self.llm = ChatOpenAI(
            model=self.settings.ai_model,
            temperature=0.7
        )

        # Create the agent
        self.agent = Agent(
            role="LinkedIn Content Creator",
            goal="Create engaging, professional LinkedIn posts that drive engagement and provide value",
            backstory="""You are a master LinkedIn content creator with years of experience crafting
            posts that resonate with professional audiences. You understand the nuances of LinkedIn's
            platform, including optimal post length, tone, formatting, and engagement tactics.
            Your posts consistently generate high engagement through compelling storytelling,
            actionable insights, and authentic voice.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def generate_content(self, topic: Dict) -> Optional[Dict]:
        """
        Generate LinkedIn content from an approved topic.

        Args:
            topic: Topic dictionary with title, outline, and metadata

        Returns:
            Dictionary with generated content and metadata
        """
        try:
            title = topic.get('title', '')
            outline = topic.get('outline', '')
            metadata = topic.get('metadata', {})

            log.info(f"Generating content for topic: {title}")

            # Create content generation task
            content_task = Task(
                description=f"""
                Create a compelling LinkedIn post based on the following topic and outline:

                **Topic**: {title}

                **Outline**:
                {outline}

                **Target Industry**: {metadata.get('industry', 'General')}

                **Requirements**:
                1. Length: {self.settings.content_min_length}-{self.settings.content_max_length} characters
                2. Format for LinkedIn:
                   - Start with a hook that grabs attention
                   - Use short paragraphs (2-3 sentences max)
                   - Include line breaks for readability
                   - Use emojis sparingly and appropriately
                   - End with a clear call-to-action or question

                3. Tone: Professional yet conversational and engaging
                4. Include:
                   - Personal insights or experiences (as thought leader)
                   - Practical takeaways
                   - Industry-relevant examples
                   - A question or CTA to drive engagement

                5. Optimize for engagement:
                   - Make it relatable
                   - Provide clear value
                   - Encourage discussion
                   - Use formatting (line breaks, emojis) strategically

                6. Do NOT:
                   - Use clickbait or sensationalism
                   - Make it too sales-y
                   - Use excessive hashtags (max 3-5 at the end)
                   - Write overly long paragraphs

                Write the complete post ready for publishing.
                """,
                agent=self.agent,
                expected_output="A complete, ready-to-publish LinkedIn post optimized for engagement"
            )

            # Create quality review task
            review_task = Task(
                description="""
                Review and refine the generated LinkedIn post:

                1. Check readability and flow
                2. Ensure it provides clear value
                3. Verify it follows LinkedIn best practices
                4. Confirm appropriate length and formatting
                5. Make sure CTA is clear and engaging
                6. Polish language and remove any redundancy

                Return the final, polished version.
                """,
                agent=self.agent,
                expected_output="A polished, publication-ready LinkedIn post",
                context=[content_task]
            )

            # Execute content generation
            crew = Crew(
                agents=[self.agent],
                tasks=[content_task, review_task],
                verbose=True
            )

            result = crew.kickoff()
            content = str(result).strip()

            # Validate content
            if not self._validate_content(content):
                log.warning("Generated content failed validation")
                return None

            # Extract hashtags if present
            hashtags = self._extract_hashtags(content)

            log.info(f"Content generated successfully. Length: {len(content)} chars")

            return {
                'content': content,
                'topic': title,
                'metadata': {
                    **metadata,
                    'generated_date': datetime.now().isoformat(),
                    'word_count': len(content.split()),
                    'char_count': len(content),
                    'hashtags': hashtags
                }
            }

        except Exception as e:
            log.error(f"Content generation failed: {str(e)}")
            return None

    def generate_variations(self, topic: Dict, num_variations: int = 3) -> list:
        """
        Generate multiple variations of content for A/B testing.

        Args:
            topic: Topic dictionary
            num_variations: Number of variations to generate

        Returns:
            List of content variations
        """
        variations = []

        try:
            tones = ["thought-provoking", "inspirational", "educational"]

            for i, tone in enumerate(tones[:num_variations]):
                log.info(f"Generating variation {i+1} with {tone} tone")

                # Temporarily modify topic for variation
                modified_topic = topic.copy()
                modified_topic['tone'] = tone

                content = self.generate_content(modified_topic)
                if content:
                    variations.append(content)

        except Exception as e:
            log.error(f"Failed to generate variations: {str(e)}")

        return variations

    def _validate_content(self, content: str) -> bool:
        """
        Validate generated content meets requirements.

        Args:
            content: Generated content string

        Returns:
            True if valid, False otherwise
        """
        if not content:
            log.warning("Content is empty")
            return False

        char_count = len(content)

        if char_count < settings.content_min_length:
            log.warning(f"Content too short: {char_count} chars")
            return False

        if char_count > settings.content_max_length:
            log.warning(f"Content too long: {char_count} chars")
            return False

        # Check for minimum engagement elements
        has_question = "?" in content
        has_line_breaks = "\n" in content

        if not has_line_breaks:
            log.warning("Content lacks proper formatting (no line breaks)")
            return False

        return True

    def _extract_hashtags(self, content: str) -> list:
        """
        Extract hashtags from content.

        Args:
            content: Content string

        Returns:
            List of hashtags
        """
        hashtags = []
        words = content.split()

        for word in words:
            if word.startswith("#"):
                hashtag = word.strip("#.,!?").lower()
                if hashtag and hashtag not in hashtags:
                    hashtags.append(hashtag)

        return hashtags

    def format_preview(self, content_dict: Dict) -> str:
        """
        Format content for preview.

        Args:
            content_dict: Content dictionary

        Returns:
            Formatted preview string
        """
        preview = "=" * 70 + "\n"
        preview += "GENERATED CONTENT PREVIEW\n"
        preview += "=" * 70 + "\n\n"

        preview += f"Topic: {content_dict.get('topic', 'N/A')}\n"
        preview += f"Generated: {content_dict.get('metadata', {}).get('generated_date', 'N/A')}\n"
        preview += f"Length: {content_dict.get('metadata', {}).get('char_count', 0)} chars, "
        preview += f"{content_dict.get('metadata', {}).get('word_count', 0)} words\n\n"

        preview += "-" * 70 + "\n\n"
        preview += content_dict.get('content', '') + "\n\n"
        preview += "-" * 70 + "\n"

        hashtags = content_dict.get('metadata', {}).get('hashtags', [])
        if hashtags:
            preview += f"\nHashtags: {', '.join(['#' + h for h in hashtags])}\n"

        preview += "\n" + "=" * 70

        return preview

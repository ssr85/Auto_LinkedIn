"""Research agent for discovering topics and creating outlines."""

from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from langchain_openai import ChatOpenAI
from typing import List, Dict, Optional, TYPE_CHECKING
from datetime import datetime
from utils.logger import log
from config import settings as default_settings

if TYPE_CHECKING:
    from config import Settings


class ResearchAgent:
    """Agent responsible for researching topics and creating outlines."""

    def __init__(self, settings: Optional["Settings"] = None):
        """Initialize the research agent.

        Args:
            settings: Settings instance to use. Defaults to global settings.
        """
        self.settings = settings or default_settings
        self.llm = ChatOpenAI(
            model=self.settings.ai_model,
            temperature=0.7
        )

        # Tools for research
        self.search_tool = SerperDevTool()
        self.scrape_tool = ScrapeWebsiteTool()

        # Create the agent
        self.agent = Agent(
            role="Content Research Specialist",
            goal="Discover trending topics and create comprehensive outlines for LinkedIn content",
            backstory="""You are an expert content researcher with deep knowledge of industry trends,
            social media engagement, and thought leadership. You excel at identifying topics that
            resonate with professionals and creating detailed outlines that guide compelling content creation.""",
            tools=[self.search_tool, self.scrape_tool],
            llm=self.settings.ai_model,
            verbose=True,
            allow_delegation=False
        )

    def research_topics(self, url: str, industry: str, num_topics: int = 5) -> List[Dict]:
        """
        Research and discover topics based on URL and industry.

        Args:
            url: Target URL to analyze
            industry: Target industry
            num_topics: Number of topics to generate

        Returns:
            List of topic dictionaries with outlines
        """
        try:
            log.info(f"Starting research for {industry} industry using {url}")

            # Create research task
            research_task = Task(
                description=f"""
                Research and identify {num_topics} compelling LinkedIn content topics for the {industry} industry.

                Follow these steps:
                1. Analyze the website: {url}
                2. Identify current trends in the {industry} industry
                3. Find topics that would engage LinkedIn professionals
                4. Ensure topics are relevant, timely, and valuable

                For each topic, provide:
                - A clear, engaging title
                - Key points to cover
                - Why it matters to the audience
                - Potential hooks or angles
                - Relevant keywords and hashtags

                Focus on:
                - Thought leadership angles
                - Practical insights
                - Industry challenges and solutions
                - Emerging trends
                - Professional development

                Return topics in a structured format.
                """,
                agent=self.agent,
                expected_output=f"A list of {num_topics} well-researched topics with detailed outlines"
            )

            # Create outline task
            outline_task = Task(
                description=f"""
                For each topic discovered, create a detailed content outline suitable for LinkedIn posts.

                Each outline should include:
                1. **Hook**: Attention-grabbing opening (1-2 sentences)
                2. **Main Points**: 3-5 key points to cover
                3. **Supporting Details**: Evidence, examples, or data for each point
                4. **Call to Action**: How readers should engage or apply the insights
                5. **Tone**: Recommended tone (professional, conversational, thought-provoking, etc.)
                6. **Hashtags**: 3-5 relevant hashtags

                Ensure outlines are:
                - Actionable and specific
                - Engaging and valuable
                - Appropriate for LinkedIn's professional audience
                - Optimized for engagement (comments, shares, likes)
                """,
                agent=self.agent,
                expected_output="Detailed, structured outlines for each topic",
                context=[research_task]
            )

            # Execute the research
            crew = Crew(
                agents=[self.agent],
                tasks=[research_task, outline_task],
                verbose=True
            )

            result = crew.kickoff()

            # Parse and structure the results
            topics = self._parse_research_results(str(result), url, industry)

            log.info(f"Research completed. Found {len(topics)} topics")
            return topics

        except Exception as e:
            log.error(f"Research failed: {str(e)}")
            return []

    def _parse_research_results(self, results: str, url: str, industry: str) -> List[Dict]:
        """
        Parse the research results into structured topic dictionaries.

        Args:
            results: Raw results from the crew
            url: Source URL
            industry: Industry name

        Returns:
            List of structured topic dictionaries
        """
        topics = []

        try:
            # Split results into individual topics
            # This is a simplified parser - you may need to adjust based on actual output
            sections = results.split("\n\n")

            current_topic = None
            for section in sections:
                section = section.strip()

                # Look for topic titles (usually marked or numbered)
                if section and (section[0].isdigit() or section.startswith("Topic") or section.startswith("#")):
                    if current_topic:
                        topics.append(current_topic)

                    # Extract title
                    lines = section.split("\n")
                    title = lines[0].strip("# 0123456789.:-").strip()

                    current_topic = {
                        'title': title,
                        'outline': section,
                        'metadata': {
                            'source_url': url,
                            'industry': industry,
                            'research_date': datetime.now().isoformat(),
                            'keywords': self._extract_keywords(section)
                        }
                    }

            # Add the last topic
            if current_topic:
                topics.append(current_topic)

            # If parsing failed, create at least one topic from the entire result
            if not topics and results:
                topics.append({
                    'title': f"{industry} Industry Insights",
                    'outline': results[:1000],  # Limit length
                    'metadata': {
                        'source_url': url,
                        'industry': industry,
                        'research_date': datetime.now().isoformat(),
                        'keywords': []
                    }
                })

        except Exception as e:
            log.error(f"Failed to parse research results: {str(e)}")

        return topics[:self.settings.max_topics_per_research]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction - look for hashtags
        keywords = []
        words = text.split()

        for word in words:
            if word.startswith("#"):
                keywords.append(word.strip("#").lower())

        return keywords[:10]

    def validate_topic(self, topic: Dict) -> bool:
        """
        Validate that a topic has all required fields.

        Args:
            topic: Topic dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'outline', 'metadata']

        for field in required_fields:
            if field not in topic:
                log.warning(f"Topic missing required field: {field}")
                return False

        return True

"""LinkedIn integration for posting content."""

from typing import Dict, Optional
import requests
from utils.logger import log
from config import settings


class LinkedInManager:
    """Manages LinkedIn API interactions for content posting."""

    def __init__(self):
        """Initialize LinkedIn client."""
        self.access_token = settings.linkedin_access_token
        self.user_id = settings.linkedin_user_id
        self.base_url = "https://api.linkedin.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def post_content(self, content: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Post content to LinkedIn.

        Args:
            content: The content to post
            metadata: Optional metadata (hashtags, mentions, etc.)

        Returns:
            Response dictionary with post details
        """
        try:
            # Prepare the post payload
            post_data = {
                "author": f"urn:li:person:{self.user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            # Add article link if provided in metadata
            if metadata and metadata.get('article_url'):
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                    "status": "READY",
                    "originalUrl": metadata['article_url']
                }]

            # Make the API request
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=self.headers,
                json=post_data,
                timeout=30
            )

            response.raise_for_status()

            post_id = response.headers.get('X-RestLi-Id', 'unknown')
            log.info(f"Successfully posted content to LinkedIn. Post ID: {post_id}")

            return {
                'success': True,
                'post_id': post_id,
                'response': response.json()
            }

        except requests.exceptions.RequestException as e:
            log.error(f"Failed to post to LinkedIn: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                log.error(f"Response: {e.response.text}")

            return {
                'success': False,
                'error': str(e)
            }

    def get_post_stats(self, post_id: str) -> Dict:
        """
        Get statistics for a LinkedIn post.

        Args:
            post_id: The LinkedIn post ID

        Returns:
            Dictionary with post statistics
        """
        try:
            response = requests.get(
                f"{self.base_url}/socialActions/{post_id}",
                headers=self.headers,
                timeout=30
            )

            response.raise_for_status()
            stats = response.json()

            log.info(f"Retrieved stats for post: {post_id}")
            return {
                'success': True,
                'stats': stats
            }

        except requests.exceptions.RequestException as e:
            log.error(f"Failed to get post stats: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def validate_token(self) -> bool:
        """
        Validate the LinkedIn access token.

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Try the modern userinfo endpoint first (best for OIDC tokens)
            response = requests.get(
                f"{self.base_url}/userinfo",
                headers=self.headers,
                timeout=30
            )

            # Fallback to /me if required
            if response.status_code != 200:
                response = requests.get(
                    f"{self.base_url}/me",
                    headers=self.headers,
                    timeout=30
                )

            response.raise_for_status()
            log.info("LinkedIn access token is valid")
            return True

        except requests.exceptions.RequestException as e:
            log.error(f"LinkedIn token validation failed: {str(e)}")
            return False

    def format_content_with_hashtags(self, content: str, hashtags: list) -> str:
        """
        Format content with hashtags.

        Args:
            content: The main content
            hashtags: List of hashtags (without #)

        Returns:
            Formatted content with hashtags
        """
        if not hashtags:
            return content

        hashtag_string = " ".join([f"#{tag}" for tag in hashtags])
        return f"{content}\n\n{hashtag_string}"

    def preview_post(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Generate a preview of how the post will look.

        Args:
            content: The content to post
            metadata: Optional metadata

        Returns:
            Formatted preview string
        """
        preview = "=" * 60 + "\n"
        preview += "LINKEDIN POST PREVIEW\n"
        preview += "=" * 60 + "\n\n"
        preview += content + "\n\n"

        if metadata:
            if metadata.get('hashtags'):
                preview += f"Hashtags: {', '.join(metadata['hashtags'])}\n"
            if metadata.get('article_url'):
                preview += f"Article Link: {metadata['article_url']}\n"

        preview += "\n" + "=" * 60

        return preview

"""LinkedIn integration for posting content."""

from typing import Dict, Optional
import requests
from utils.logger import log
from config import settings


class LinkedInManager:
    """Manages LinkedIn API interactions for content posting."""

    def __init__(self):
        """Initialize LinkedIn client."""
        self.client_id = settings.linkedin_client_id
        self.client_secret = settings.linkedin_client_secret
        self.access_token = settings.linkedin_access_token
        self.user_id = settings.linkedin_user_id
        self.base_url = "https://api.linkedin.com/v2"
        self.headers = {}
        self._set_headers()

    def _set_headers(self):
        """Set headers for API requests."""
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def _ensure_authenticated_request(self, method: str, url: str, **kwargs):
        """Make an API request and refresh token if needed."""
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            if response.status_code == 401:
                log.error("LinkedIn access token expired. Please run 'python get_linkedin_token.py' to generate a new one.")
            return response
        except Exception as e:
            log.error(f"Request failed: {str(e)}")
            raise


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
                from typing import cast, Any
                specific_content = cast(dict[str, Any], post_data["specificContent"])
                share_content = cast(dict[str, Any], specific_content["com.linkedin.ugc.ShareContent"])
                share_content["shareMediaCategory"] = "ARTICLE"
                share_content["media"] = [{
                    "status": "READY",
                    "originalUrl": metadata['article_url']
                }]

            # Make the API request using the authenticated wrapper
            response = self._ensure_authenticated_request(
                "POST",
                f"{self.base_url}/ugcPosts",
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
                log.error(f"Response: {cast(requests.Response, e.response).text}")

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
            response = self._ensure_authenticated_request(
                "GET",
                f"{self.base_url}/socialActions/{post_id}",
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
            response = self._ensure_authenticated_request(
                "GET",
                f"{self.base_url}/userinfo",
                timeout=30
            )

            # Fallback to /me if required
            if response.status_code != 200:
                response = self._ensure_authenticated_request(
                    "GET",
                    f"{self.base_url}/me",
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

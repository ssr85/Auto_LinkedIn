#!/usr/bin/env python3
"""
Helper script to get LinkedIn OAuth token.
This creates a simple server to handle the OAuth callback.
"""

import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys

# You need to set these from your LinkedIn App
CLIENT_ID = input("Enter your LinkedIn App Client ID: ").strip()
CLIENT_SECRET = input("Enter your LinkedIn App Client Secret: ").strip()
REDIRECT_URI = "http://localhost:8000/callback"

# OAuth URLs
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# Store the authorization code
auth_code = None


class OAuthHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback."""

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        global auth_code

        # Parse the URL
        parsed = urlparse(self.path)

        if parsed.path == "/callback":
            # Extract the authorization code
            params = parse_qs(parsed.query)

            if "code" in params:
                auth_code = params["code"][0]

                # Send success response
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                html = """
                <html>
                <head><title>Success!</title></head>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())

            elif "error" in params:
                # Handle error
                error = params["error"][0]
                error_desc = params.get("error_description", ["Unknown error"])[0]

                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                html = f"""
                <html>
                <head><title>Error</title></head>
                <body>
                    <h1>Authorization Failed</h1>
                    <p><strong>Error:</strong> {error}</p>
                    <p><strong>Description:</strong> {error_desc}</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def get_access_token(auth_code):
    """Exchange authorization code for access token."""
    import requests

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting access token: {response.text}")
        return None


def get_user_info(access_token):
    """Get user profile information."""
    import requests

    headers = {"Authorization": f"Bearer {access_token}"}

    # Try the newer userinfo endpoint first (required for openid scope)
    response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    
    # Fallback to /v2/me if original endpoint is preferred
    if response.status_code != 200:
        response = requests.get("https://api.linkedin.com/v2/me", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting user info: {response.text}")
        return None


def main():
    """Main OAuth flow."""
    global auth_code

    print("\n" + "=" * 60)
    print("LinkedIn OAuth Token Generator")
    print("=" * 60 + "\n")

    # Build authorization URL
    # Use newer OpenID Connect scopes (more likely to be approved by default)
    scopes = "openid profile w_member_social"
    auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={scopes}"

    print("Step 1: Opening browser for LinkedIn authorization...")
    print(f"\nIf browser doesn't open, visit this URL:\n{auth_url}\n")

    # Open browser
    webbrowser.open(auth_url)

    # Start local server
    print("Step 2: Starting local server to receive callback...")
    print("Listening on http://localhost:8000\n")

    server = HTTPServer(("localhost", 8000), OAuthHandler)

    # Wait for callback
    print("Waiting for authorization... (this may take a moment)")
    while auth_code is None:
        server.handle_request()

    print("\n✓ Authorization code received!")

    # Exchange code for token
    print("\nStep 3: Exchanging code for access token...")

    token_data = get_access_token(auth_code)

    if not token_data:
        print("✗ Failed to get access token")
        sys.exit(1)

    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", "unknown")

    print(f"✓ Access token obtained! (Expires in {expires_in} seconds)")

    # Get user info
    print("\nStep 4: Getting user information...")

    user_info = get_user_info(access_token)

    if user_info:
        user_id = user_info.get("id")
        print(f"✓ User ID: {user_id}")
    else:
        print("⚠️  Could not retrieve user ID")
        user_id = "unknown"

    # Display results
    print("\n" + "=" * 60)
    print("SUCCESS! Add these to your .env file:")
    print("=" * 60)
    print(f"\nLINKEDIN_ACCESS_TOKEN={access_token}")
    print(f"LINKEDIN_USER_ID={user_id}")
    print("\n" + "=" * 60)

    print("\n⚠️  Important Notes:")
    print("1. This token will expire - check your app for expiration time")
    print("2. Keep this token secure - don't share it")
    print("3. If you need a longer-lived token, implement token refresh")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)

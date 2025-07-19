import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


class GitHubApp:
    """
    A class to handle GitHub App authentication and API interactions
    """

    def __init__(
        self, app_id: str, private_key_path: str, installation_id: Optional[str] = None
    ):
        """
        Initialize GitHub App with credentials

        Args:
            app_id: GitHub App ID
            private_key_path: Path to the private key .pem file
            installation_id: Installation ID (optional, can be set later)
        """
        self.app_id = app_id
        self.private_key_path = private_key_path
        self.installation_id = installation_id
        self.private_key = self._load_private_key()
        self._installation_token = None
        self._token_expires_at = None

    def _load_private_key(self) -> bytes:
        """Load and return the private key from file"""
        with open(self.private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )
        return private_key

    def generate_jwt(self) -> str:
        """
        Generate a JWT token for GitHub App authentication

        Returns:
            JWT token string
        """
        # JWT expiration time (10 minutes maximum for GitHub Apps)
        now = int(time.time())
        expiration = now + (10 * 60)  # 10 minutes

        # Create JWT payload
        payload = {"iat": now, "exp": expiration, "iss": self.app_id}

        # Sign and encode the JWT
        encoded_jwt = jwt.encode(payload, self.private_key, algorithm="RS256")

        return encoded_jwt

    def get_installations(self) -> Dict[str, Any]:
        """
        Get all installations for this GitHub App

        Returns:
            Dictionary containing installation data
        """
        jwt_token = self.generate_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(
            "https://api.github.com/app/installations", headers=headers
        )
        response.raise_for_status()
        return response.json()

    def get_installation_token(self, force_refresh: bool = False) -> str:
        """
        Get or refresh installation access token

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            Installation access token
        """
        if not self.installation_id:
            raise ValueError("Installation ID is required to get installation token")

        # Check if we have a valid cached token
        if not force_refresh and self._installation_token and self._token_expires_at:
            # Use timezone-aware datetime for comparison
            if datetime.now(timezone.utc) < self._token_expires_at:
                return self._installation_token

        # Generate new installation token
        jwt_token = self.generate_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.post(
            f"https://api.github.com/app/installations/{self.installation_id}/access_tokens",
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        self._installation_token = data["token"]

        # Parse expiration time - handle both 'Z' suffix and '+00:00' offset
        expires_at_str = data["expires_at"]
        if expires_at_str.endswith("Z"):
            expires_at_str = expires_at_str[:-1] + "+00:00"

        # Parse as timezone-aware datetime
        expires_at = datetime.fromisoformat(expires_at_str)

        # Ensure it's UTC if no timezone info (shouldn't happen with GitHub API)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # Set expiration 5 minutes earlier for safety
        self._token_expires_at = expires_at - timedelta(minutes=5)

        return self._installation_token

    def make_api_request(
        self, method: str, endpoint: str, **kwargs
    ) -> requests.Response:
        """
        Make an authenticated API request to GitHub

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., '/repos/owner/repo/contents/file.txt')
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object
        """
        token = self.get_installation_token()

        # Set default headers
        headers = kwargs.get("headers", {})
        headers.update(
            {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }
        )
        kwargs["headers"] = headers

        # Make the request
        url = f"https://api.github.com{endpoint}"
        response = requests.request(method, url, **kwargs)

        # Handle token expiration
        if response.status_code == 401:
            # Token might be expired, try refreshing
            token = self.get_installation_token(force_refresh=True)
            headers["Authorization"] = f"token {token}"
            response = requests.request(method, url, **kwargs)

        return response

    def get_repository_content(
        self, owner: str, repo: str, path: str = ""
    ) -> Dict[str, Any]:
        """
        Get repository content at specified path

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path to file or directory

        Returns:
            Repository content data
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        response = self.make_api_request("GET", endpoint)
        response.raise_for_status()
        return response.json()

    def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create or update a file in the repository

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content (will be base64 encoded)
            message: Commit message
            sha: SHA of the file to update (required for updates)

        Returns:
            API response data
        """
        import base64

        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
        }

        if sha:
            data["sha"] = sha

        response = self.make_api_request("PUT", endpoint, json=data)
        response.raise_for_status()
        return response.json()


# Example wrapper for Jenkins integration
class GitHubAppJenkinsHelper:
    """
    Helper class for Jenkins-specific GitHub App operations
    """

    def __init__(self, github_app: GitHubApp):
        self.github_app = github_app

    def get_credentials_for_jenkins(self) -> Dict[str, str]:
        """
        Get credentials in a format suitable for Jenkins

        Returns:
            Dictionary with token and metadata
        """
        token = self.github_app.get_installation_token()
        return {
            "token": token,
            "token_type": "installation",
            "expires_at": (
                self.github_app._token_expires_at.isoformat()
                if self.github_app._token_expires_at
                else None
            ),
        }

    def clone_repository_command(self, owner: str, repo: str) -> str:
        """
        Generate a git clone command with authentication

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Git clone command with embedded token
        """
        token = self.github_app.get_installation_token()
        return f"git clone https://x-access-token:{token}@github.com/{owner}/{repo}.git"

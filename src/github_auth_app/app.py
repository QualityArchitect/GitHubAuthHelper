import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, cast

import jwt
import requests
from cryptography.hazmat.primitives import serialization

from .config import Config

logger = logging.getLogger(__name__)


class GitHubApp:
    """Handles GitHub App authentication and token management."""

    def __init__(self, config: Config):
        """Initialize GitHub App with configuration."""
        self.config = config
        self._private_key: Optional[bytes] = None
        self._token_cache: Dict[str, Dict[str, Any]] = {}

    def _load_private_key(self) -> bytes:
        """Load and cache the private key."""
        if self._private_key is None:
            key_path = Path(self.config.private_key_path)
            if not key_path.exists():
                raise FileNotFoundError(f"Private key not found at {key_path}")

            with open(key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(), password=None
                )
                # Serialize the key back to PEM format bytes
                self._private_key = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
        return self._private_key

    def _create_jwt(self) -> str:
        """Create a JWT for GitHub App authentication."""
        private_key = self._load_private_key()
        now = int(time.time())

        payload = {
            "iat": now,
            "exp": now + 600,  # 10 minutes
            "iss": self.config.app_id,
        }

        return jwt.encode(payload, private_key, algorithm="RS256")

    def _make_github_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make a request to GitHub API with error handling."""
        if headers is None:
            headers = {}

        headers.update(
            {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": f"GitHubApp/{self.config.app_id}",
            }
        )

        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return cast(Dict[str, Any], response.json())

    def get_app_info(self) -> Dict[str, Any]:
        """Get information about the GitHub App."""
        jwt_token = self._create_jwt()
        return self._make_github_request(
            "GET",
            "https://api.github.com/app",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    def get_installation_id(self, owner: str, repo: str) -> Optional[int]:
        """Get installation ID for a specific repository."""
        jwt_token = self._create_jwt()

        try:
            data = self._make_github_request(
                "GET",
                f"https://api.github.com/repos/{owner}/{repo}/installation",
                headers={"Authorization": f"Bearer {jwt_token}"},
            )
            return int(data["id"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"No installation found for {owner}/{repo}")
                return None
            raise

    def get_installation_token(
        self, installation_id: int, permissions: Optional[Dict[str, str]] = None
    ) -> str:
        """Get an installation access token."""
        cache_key = f"token_{installation_id}"

        # Check cache
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            expires_at = cached.get("expires_at")
            if expires_at and isinstance(expires_at, datetime):
                if datetime.now(timezone.utc) < expires_at - timedelta(minutes=5):
                    return str(cached["token"])

        # Create new token
        jwt_token = self._create_jwt()
        url = (
            f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        )

        body: Dict[str, Any] = {}
        if permissions:
            body["permissions"] = permissions

        data = self._make_github_request(
            "POST",
            url,
            headers={"Authorization": f"Bearer {jwt_token}"},
            json=body if body else None,
        )

        # Cache the token
        expires_at_str = data.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            self._token_cache[cache_key] = {
                "token": data["token"],
                "expires_at": expires_at,
            }

        return str(data["token"])

    def get_repository_token(self, owner: str, repo: str) -> Optional[str]:
        """Get an installation token for a specific repository."""
        installation_id = self.get_installation_id(owner, repo)
        if installation_id is None:
            return None

        return self.get_installation_token(installation_id)

    def create_check_run(
        self,
        owner: str,
        repo: str,
        name: str,
        head_sha: str,
        status: str = "queued",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a check run for a commit."""
        token = self.get_repository_token(owner, repo)
        if not token:
            raise ValueError(f"No installation found for {owner}/{repo}")

        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs"
        body = {
            "name": name,
            "head_sha": head_sha,
            "status": status,
            **kwargs,
        }

        return self._make_github_request(
            "POST", url, headers={"Authorization": f"token {token}"}, json=body
        )

    def update_check_run(
        self, owner: str, repo: str, check_run_id: int, **kwargs: Any
    ) -> Dict[str, Any]:
        """Update an existing check run."""
        token = self.get_repository_token(owner, repo)
        if not token:
            raise ValueError(f"No installation found for {owner}/{repo}")

        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs/{check_run_id}"

        return self._make_github_request(
            "PATCH", url, headers={"Authorization": f"token {token}"}, json=kwargs
        )

    def create_deployment(
        self,
        owner: str,
        repo: str,
        ref: str,
        environment: str = "production",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a deployment."""
        token = self.get_repository_token(owner, repo)
        if not token:
            raise ValueError(f"No installation found for {owner}/{repo}")

        url = f"https://api.github.com/repos/{owner}/{repo}/deployments"
        body = {
            "ref": ref,
            "environment": environment,
            "auto_merge": False,
            **kwargs,
        }

        return self._make_github_request(
            "POST", url, headers={"Authorization": f"token {token}"}, json=body
        )

    def create_deployment_status(
        self,
        owner: str,
        repo: str,
        deployment_id: int,
        state: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a deployment status."""
        token = self.get_repository_token(owner, repo)
        if not token:
            raise ValueError(f"No installation found for {owner}/{repo}")

        url = f"https://api.github.com/repos/{owner}/{repo}/deployments/{deployment_id}/statuses"
        body = {"state": state, **kwargs}

        return self._make_github_request(
            "POST", url, headers={"Authorization": f"token {token}"}, json=body
        )

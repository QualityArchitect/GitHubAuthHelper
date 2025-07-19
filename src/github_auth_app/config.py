"""Configuration module for GitHub App."""

import os
from typing import Optional


class Config:
    """Configuration for GitHub App authentication."""

    def __init__(
        self,
        app_id: Optional[str] = None,
        private_key_path: Optional[str] = None,
        installation_id: Optional[str] = None,
    ):
        """
        Initialize configuration.

        Args:
            app_id: GitHub App ID (defaults to GITHUB_APP_ID env var)
            private_key_path: Path to private key (defaults to GITHUB_APP_PRIVATE_KEY_PATH env var)
            installation_id: Installation ID (defaults to GITHUB_APP_INSTALLATION_ID env var)
        """
        self.app_id = app_id or os.environ.get("GITHUB_APP_ID")
        self.private_key_path = private_key_path or os.environ.get(
            "GITHUB_APP_PRIVATE_KEY_PATH"
        )
        self.installation_id = installation_id or os.environ.get(
            "GITHUB_APP_INSTALLATION_ID"
        )

        # Validate required fields
        if not self.app_id:
            raise ValueError(
                "GitHub App ID is required. Set GITHUB_APP_ID environment variable or pass app_id parameter."
            )
        if not self.private_key_path:
            raise ValueError(
                "Private key path is required. Set GITHUB_APP_PRIVATE_KEY_PATH environment variable or pass private_key_path parameter."
            )

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()

    def __repr__(self) -> str:
        """String representation of config."""
        return (
            f"Config(app_id={self.app_id!r}, "
            f"private_key_path={self.private_key_path!r}, "
            f"installation_id={self.installation_id!r})"
        )

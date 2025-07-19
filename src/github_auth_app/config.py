"""Configuration module for GitHub App authentication."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration for GitHub App authentication."""

    app_id: str
    private_key_path: str
    installation_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        app_id = os.getenv("GITHUB_APP_ID")
        if not app_id:
            raise ValueError("GITHUB_APP_ID environment variable is required")

        private_key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
        if not private_key_path:
            raise ValueError(
                "GITHUB_APP_PRIVATE_KEY_PATH environment variable is required"
            )

        # Expand user home directory if present
        private_key_path = str(Path(private_key_path).expanduser())

        installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")

        return cls(
            app_id=app_id,
            private_key_path=private_key_path,
            installation_id=installation_id,
        )

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate app_id is numeric
        try:
            int(self.app_id)
        except ValueError:
            raise ValueError(f"app_id must be numeric, got: {self.app_id}")

        # Validate private key path exists
        key_path = Path(self.private_key_path)
        if not key_path.exists():
            raise FileNotFoundError(
                f"Private key file not found: {self.private_key_path}"
            )

        # Validate installation_id if provided
        if self.installation_id is not None:
            try:
                int(self.installation_id)
            except ValueError:
                raise ValueError(
                    f"installation_id must be numeric, got: {self.installation_id}"
                )


# For convenience, create a default config instance
def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config.from_env()

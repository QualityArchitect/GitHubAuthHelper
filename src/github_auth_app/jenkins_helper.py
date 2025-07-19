"""Jenkins helper script for GitHub App authentication."""

import argparse
import json
import logging
import sys
from typing import Dict, Optional

from .app import GitHubApp
from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubAppJenkinsHelper:
    """Helper class for Jenkins-specific GitHub App operations."""

    def __init__(self, github_app: GitHubApp):
        """Initialize with a GitHubApp instance."""
        self.github_app = github_app

    def get_credentials_for_jenkins(
        self, owner: str, repo: str
    ) -> Dict[str, Optional[str]]:
        """
        Get credentials in a format suitable for Jenkins.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with token and metadata
        """
        token = self.github_app.get_repository_token(owner, repo)
        if token is None:
            return {
                "token": None,
                "token_type": None,
                "expires_at": None,
                "error": f"No installation found for {owner}/{repo}",
            }

        # Get expiration from cache if available
        installation_id = self.github_app.get_installation_id(owner, repo)
        expires_at = None

        if installation_id is not None:
            cache_key = f"token_{installation_id}"
            if cache_key in self.github_app._token_cache:
                cached = self.github_app._token_cache[cache_key]
                expires_datetime = cached.get("expires_at")
                if expires_datetime:
                    expires_at = expires_datetime.isoformat()

        return {
            "token": token,
            "token_type": "installation",
            "expires_at": expires_at,
        }

    def clone_repository_command(self, owner: str, repo: str) -> Optional[str]:
        """
        Generate a git clone command with authentication.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Git clone command with embedded token, or None if no token available
        """
        token = self.github_app.get_repository_token(owner, repo)
        if token is None:
            return None
        return f"git clone https://x-access-token:{token}@github.com/{owner}/{repo}.git"


def main() -> None:
    """CLI entry point for Jenkins integration."""
    parser = argparse.ArgumentParser(description="GitHub App authentication helper")
    parser.add_argument("owner", help="Repository owner")
    parser.add_argument("repo", help="Repository name")
    parser.add_argument(
        "--output-format",
        choices=["token", "json", "env", "clone"],
        default="token",
        help="Output format",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        config = Config()
        app = GitHubApp(config)
        helper = GitHubAppJenkinsHelper(app)

        if args.output_format == "clone":
            clone_cmd = helper.clone_repository_command(args.owner, args.repo)
            if clone_cmd is None:
                logger.error(f"No installation found for {args.owner}/{args.repo}")
                sys.exit(1)
            print(clone_cmd)
        else:
            token = app.get_repository_token(args.owner, args.repo)
            if token is None:
                logger.error(f"No installation found for {args.owner}/{args.repo}")
                sys.exit(1)

            if args.output_format == "token":
                print(token)
            elif args.output_format == "json":
                creds = helper.get_credentials_for_jenkins(args.owner, args.repo)
                print(json.dumps(creds, indent=2))
            elif args.output_format == "env":
                print(f"GITHUB_TOKEN={token}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()

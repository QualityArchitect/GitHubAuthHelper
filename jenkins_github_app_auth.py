#!/usr/bin/env python3
"""
Script to be used in Jenkins to get GitHub App authentication
Can be used in Jenkins Pipeline or as a credential provider
"""

import argparse
import json
import sys
from typing import Optional

from src.github_auth_app.app import GitHubApp
from src.github_auth_app.config import Config


def main():
    parser = argparse.ArgumentParser(description="Get GitHub App token for Jenkins")
    parser.add_argument("--app-id", required=True, help="GitHub App ID")
    parser.add_argument("--private-key-path", required=True, help="Path to private key")
    parser.add_argument("--installation-id", required=True, help="Installation ID")
    parser.add_argument(
        "--output-format",
        choices=["token", "json", "export"],
        default="token",
        help="Output format",
    )

    args = parser.parse_args()

    try:
        # Create configuration
        config = Config(
            app_id=args.app_id,
            private_key_path=args.private_key_path,
            installation_id=args.installation_id,
        )

        # Initialize GitHub App
        app = GitHubApp(config)

        # Get token
        token = app.get_installation_token(int(args.installation_id))

        # Get expiration from cache if available
        expires_at: Optional[str] = None
        cache_key = f"token_{args.installation_id}"
        if cache_key in app._token_cache:
            cached = app._token_cache[cache_key]
            expires_datetime = cached.get("expires_at")
            if expires_datetime:
                expires_at = expires_datetime.isoformat()

        # Output in requested format
        if args.output_format == "token":
            print(token)
        elif args.output_format == "json":
            print(
                json.dumps(
                    {
                        "token": token,
                        "expires_at": expires_at,
                    }
                )
            )
        elif args.output_format == "export":
            print(f'export GITHUB_TOKEN="{token}"')

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

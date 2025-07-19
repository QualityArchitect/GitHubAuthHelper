# !/usr/bin/env python3
"""
Script to be used in Jenkins to get GitHub App authentication
Can be used in Jenkins Pipeline or as a credential provider
"""

import argparse
import json
import sys

from src.github_auth_app.app import GitHubApp


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
        # Initialize GitHub App
        app = GitHubApp(
            app_id=args.app_id,
            private_key_path=args.private_key_path,
            installation_id=args.installation_id,
        )

        # Get token
        token = app.get_installation_token()

        # Output in requested format
        if args.output_format == "token":
            print(token)
        elif args.output_format == "json":
            print(
                json.dumps(
                    {
                        "token": token,
                        "expires_at": (
                            app._token_expires_at.isoformat()
                            if app._token_expires_at
                            else None
                        ),
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

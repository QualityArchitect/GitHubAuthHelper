from typing import Dict

from .app import GitHubApp


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


def main():
    """CLI entry point for Jenkins integration"""
    import argparse
    import json
    import sys

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
        app = GitHubApp(
            app_id=args.app_id,
            private_key_path=args.private_key_path,
            installation_id=args.installation_id,
        )

        helper = GitHubAppJenkinsHelper(app)
        token = app.get_installation_token()

        if args.output_format == "token":
            print(token)
        elif args.output_format == "json":
            creds = helper.get_credentials_for_jenkins()
            print(json.dumps(creds))
        elif args.output_format == "export":
            print(f'export GITHUB_TOKEN="{token}"')

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

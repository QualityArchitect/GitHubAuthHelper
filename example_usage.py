from src.github_auth_app import GitHubApp, GitHubAppJenkinsHelper
from src.github_auth_app.config import (
    GITHUB_APP_ID,
    GITHUB_APP_INSTALLATION_ID,
    GITHUB_APP_PRIVATE_KEY_PATH,
)


def main():
    # Initialize GitHub App
    app = GitHubApp(
        app_id=GITHUB_APP_ID,
        private_key_path=GITHUB_APP_PRIVATE_KEY_PATH,
        installation_id=GITHUB_APP_INSTALLATION_ID,
    )

    # Example 1: List installations (if you don't know your installation ID)
    if not GITHUB_APP_INSTALLATION_ID:
        installations = app.get_installations()
        print("Available installations:")
        for installation in installations:
            print(
                f"- ID: {installation['id']}, Account: {installation['account']['login']}"
            )

        # Set the installation ID for the first installation
        if installations:
            app.installation_id = str(installations[0]["id"])

    # Example 2: Get repository contents
    try:
        contents = app.get_repository_content("your-org", "your-repo", "README.md")
        print(f"README.md SHA: {contents.get('sha')}")
    except Exception as e:
        print(f"Error getting repository content: {e}")

    # Example 3: Create/Update a file
    try:
        result = app.create_or_update_file(
            owner="your-org",
            repo="your-repo",
            path="test-file.txt",
            content="Hello from GitHub App!",
            message="Test commit from GitHub App",
        )
        print(f"File created/updated: {result['content']['path']}")
    except Exception as e:
        print(f"Error creating/updating file: {e}")

    # Example 4: Jenkins integration
    jenkins_helper = GitHubAppJenkinsHelper(app)

    # Get credentials for Jenkins
    jenkins_creds = jenkins_helper.get_credentials_for_jenkins()
    print(f"Jenkins token: {jenkins_creds['token'][:10]}...")

    # Get clone command
    clone_cmd = jenkins_helper.clone_repository_command("your-org", "your-repo")
    print(f"Clone command: {clone_cmd[:50]}...")


if __name__ == "__main__":
    main()

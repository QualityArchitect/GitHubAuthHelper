from datetime import datetime, timedelta, timezone

import pytest
import responses

from github_app_auth import GitHubApp, GitHubAppJenkinsHelper


@pytest.mark.integration
class TestGitHubAppIntegration:
    """Integration tests that mock actual GitHub API responses"""

    @pytest.fixture
    def github_app(self, private_key_file):
        """Create a real GitHubApp instance with mocked API"""
        return GitHubApp(
            app_id="123456", private_key_path=private_key_file, installation_id="789012"
        )

    @responses.activate
    def test_full_workflow(self, github_app):
        """Test complete workflow from authentication to API usage"""
        # Use a future expiration date
        future_date = (
            (datetime.now(timezone.utc) + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z")
        )

        # Mock installation token endpoint
        responses.add(
            responses.POST,
            "https://api.github.com/app/installations/789012/access_tokens",
            json={"token": "ghs_integration_test_token", "expires_at": future_date},
            status=201,
        )

        # Mock repository content endpoint
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test-org/test-repo/contents/README.md",
            json={
                "name": "README.md",
                "content": "IyBUZXN0IFJlcG8=",  # Base64: "# Test Repo"
                "sha": "abc123",
            },
            status=200,
        )

        # Get installation token
        token = github_app.get_installation_token()
        assert token == "ghs_integration_test_token"

        # Use token to get repository content
        content = github_app.get_repository_content(
            "test-org", "test-repo", "README.md"
        )
        assert content["name"] == "README.md"
        assert content["sha"] == "abc123"

        # Verify the correct headers were sent
        assert len(responses.calls) == 2
        assert "Authorization" in responses.calls[1].request.headers
        assert (
            responses.calls[1].request.headers["Authorization"]
            == "token ghs_integration_test_token"
        )

    @responses.activate
    def test_jenkins_integration(self, github_app):
        """Test Jenkins helper integration"""
        # Use a future expiration date
        future_date = (
            (datetime.now(timezone.utc) + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z")
        )

        # Mock installation token endpoint
        responses.add(
            responses.POST,
            "https://api.github.com/app/installations/789012/access_tokens",
            json={"token": "ghs_jenkins_token", "expires_at": future_date},
            status=201,
        )

        helper = GitHubAppJenkinsHelper(github_app)

        # Get credentials for Jenkins
        creds = helper.get_credentials_for_jenkins()
        assert creds["token"] == "ghs_jenkins_token"
        assert creds["token_type"] == "installation"

        # Get clone command
        clone_cmd = helper.clone_repository_command("test-org", "test-repo")
        assert "x-access-token:ghs_jenkins_token" in clone_cmd

        # Verify only one token request was made (due to caching)
        assert len(responses.calls) == 1

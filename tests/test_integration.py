from datetime import datetime, timedelta, timezone

import pytest
import responses

from src.github_auth_app.app import GitHubApp
from src.github_auth_app.config import Config
from src.github_auth_app.jenkins_helper import GitHubAppJenkinsHelper


@pytest.mark.integration
class TestGitHubAppIntegration:
    """Integration tests that mock actual GitHub API responses"""

    @pytest.fixture
    def github_app(self, private_key_file):
        """Create a real GitHubApp instance with mocked API"""
        config = Config(
            app_id="123456", private_key_path=private_key_file, installation_id="789012"
        )
        return GitHubApp(config)

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

        # Mock repository installation endpoint
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test-org/test-repo/installation",
            json={"id": 789012},
            status=200,
        )

        # Mock check run creation endpoint
        responses.add(
            responses.POST,
            "https://api.github.com/repos/test-org/test-repo/check-runs",
            json={
                "id": 4,
                "head_sha": "ce587453ced02b1526dfb4cb910479d431683101",
                "status": "queued",
                "name": "test-check",
            },
            status=201,
        )

        # Get installation token
        token = github_app.get_installation_token(789012)
        assert token == "ghs_integration_test_token"

        # Create a check run
        check_run = github_app.create_check_run(
            "test-org",
            "test-repo",
            "test-check",
            "ce587453ced02b1526dfb4cb910479d431683101",
        )
        assert check_run["id"] == 4
        assert check_run["status"] == "queued"

        # Verify the correct headers were sent
        assert len(responses.calls) == 3
        assert "Authorization" in responses.calls[2].request.headers
        assert (
            responses.calls[2].request.headers["Authorization"]
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

        # Mock installation endpoint
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test-org/test-repo/installation",
            json={"id": 789012},
            status=200,
        )

        # Mock installation token endpoint
        responses.add(
            responses.POST,
            "https://api.github.com/app/installations/789012/access_tokens",
            json={"token": "ghs_jenkins_test_token", "expires_at": future_date},
            status=201,
        )

        # Create Jenkins helper
        helper = GitHubAppJenkinsHelper(github_app)

        # Test getting credentials
        creds = helper.get_credentials_for_jenkins("test-org", "test-repo")
        assert creds["token"] == "ghs_jenkins_test_token"
        assert creds["token_type"] == "installation"
        assert creds["expires_at"] is not None

        # Test clone command generation
        clone_cmd = helper.clone_repository_command("test-org", "test-repo")
        assert (
            clone_cmd
            == "git clone https://x-access-token:ghs_jenkins_test_token@github.com/test-org/test-repo.git"
        )

    @responses.activate
    def test_token_expiration_handling(self, github_app):
        """Test that expired tokens are refreshed"""
        # First token - expires soon
        soon_expiry = (
            (datetime.now(timezone.utc) + timedelta(minutes=3))
            .isoformat()
            .replace("+00:00", "Z")
        )

        # Second token - expires in an hour
        later_expiry = (
            (datetime.now(timezone.utc) + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z")
        )

        # Mock first token response
        responses.add(
            responses.POST,
            "https://api.github.com/app/installations/789012/access_tokens",
            json={"token": "ghs_first_token", "expires_at": soon_expiry},
            status=201,
        )

        # Get first token
        token1 = github_app.get_installation_token(789012)
        assert token1 == "ghs_first_token"

        # Mock second token response
        responses.add(
            responses.POST,
            "https://api.github.com/app/installations/789012/access_tokens",
            json={"token": "ghs_second_token", "expires_at": later_expiry},
            status=201,
        )

        # Get token again - should get new one due to expiration
        token2 = github_app.get_installation_token(789012)
        assert token2 == "ghs_second_token"
        assert len(responses.calls) == 2

    @responses.activate
    def test_repository_not_installed(self, github_app):
        """Test handling of repositories without app installation"""
        # Mock 404 response for installation lookup
        responses.add(
            responses.GET,
            "https://api.github.com/repos/uninstalled-org/uninstalled-repo/installation",
            status=404,
        )

        # Try to get token for uninstalled repo
        token = github_app.get_repository_token("uninstalled-org", "uninstalled-repo")
        assert token is None

        # Try to create check run for uninstalled repo
        with pytest.raises(ValueError, match="No installation found"):
            github_app.create_check_run(
                "uninstalled-org",
                "uninstalled-repo",
                "test-check",
                "abc123",
            )

    @responses.activate
    def test_deployment_workflow(self, github_app):
        """Test deployment creation and status updates"""
        # Setup token
        future_date = (
            (datetime.now(timezone.utc) + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z")
        )

        responses.add(
            responses.GET,
            "https://api.github.com/repos/test-org/test-repo/installation",
            json={"id": 789012},
            status=200,
        )

        responses.add(
            responses.POST,
            "https://api.github.com/app/installations/789012/access_tokens",
            json={"token": "ghs_deployment_token", "expires_at": future_date},
            status=201,
        )

        # Mock deployment creation
        responses.add(
            responses.POST,
            "https://api.github.com/repos/test-org/test-repo/deployments",
            json={
                "id": 1,
                "ref": "main",
                "environment": "production",
                "statuses_url": "https://api.github.com/repos/test-org/test-repo/deployments/1/statuses",
            },
            status=201,
        )

        # Mock deployment status update
        responses.add(
            responses.POST,
            "https://api.github.com/repos/test-org/test-repo/deployments/1/statuses",
            json={
                "id": 1,
                "state": "success",
                "deployment_id": 1,
            },
            status=201,
        )

        # Create deployment
        deployment = github_app.create_deployment(
            "test-org", "test-repo", "main", "production"
        )
        assert deployment["id"] == 1
        assert deployment["environment"] == "production"

        # Update deployment status
        status = github_app.create_deployment_status(
            "test-org", "test-repo", 1, "success", description="Deployed successfully"
        )
        assert status["state"] == "success"
        assert status["deployment_id"] == 1

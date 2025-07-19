from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from github_auth_app.app import GitHubApp
from github_auth_app.jenkins_helper import GitHubAppJenkinsHelper


class TestGitHubAppJenkinsHelper:
    """Test cases for GitHubAppJenkinsHelper class."""

    @pytest.fixture
    def mock_github_app(self):
        """Create a mock GitHubApp instance."""
        app = Mock(spec=GitHubApp)
        app.get_repository_token.return_value = "test_token_123456"
        app.get_installation_id.return_value = 12345
        app._token_cache = {
            "token_12345": {
                "token": "test_token_123456",
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            }
        }
        return app

    def test_initialization(self, mock_github_app):
        """Test helper initialization."""
        helper = GitHubAppJenkinsHelper(mock_github_app)
        assert helper.github_app == mock_github_app

    def test_get_credentials_for_jenkins(self, mock_github_app):
        """Test getting credentials in Jenkins format."""
        helper = GitHubAppJenkinsHelper(mock_github_app)

        creds = helper.get_credentials_for_jenkins("test-org", "test-repo")

        assert creds["token"] == "test_token_123456"
        assert creds["token_type"] == "installation"
        assert creds["expires_at"] is not None
        assert isinstance(creds["expires_at"], str)

        # Verify token was requested
        mock_github_app.get_repository_token.assert_called_once_with(
            "test-org", "test-repo"
        )
        mock_github_app.get_installation_id.assert_called_once_with(
            "test-org", "test-repo"
        )

    def test_get_credentials_for_jenkins_no_token(self, mock_github_app):
        """Test getting credentials when no token is available."""
        mock_github_app.get_repository_token.return_value = None
        helper = GitHubAppJenkinsHelper(mock_github_app)

        creds = helper.get_credentials_for_jenkins("test-org", "test-repo")

        assert creds["token"] is None
        assert creds["token_type"] is None
        assert creds["expires_at"] is None
        assert "error" in creds
        assert "No installation found" in creds["error"]

    def test_get_credentials_for_jenkins_no_cache(self, mock_github_app):
        """Test getting credentials when token is not in cache."""
        mock_github_app._token_cache = {}
        helper = GitHubAppJenkinsHelper(mock_github_app)

        creds = helper.get_credentials_for_jenkins("test-org", "test-repo")

        assert creds["token"] == "test_token_123456"
        assert creds["expires_at"] is None  # No cache, so no expiration info

    def test_clone_repository_command(self, mock_github_app):
        """Test generating clone command with authentication."""
        helper = GitHubAppJenkinsHelper(mock_github_app)

        clone_cmd = helper.clone_repository_command("test-org", "test-repo")

        expected = "git clone https://x-access-token:test_token_123456@github.com/test-org/test-repo.git"
        assert clone_cmd == expected

        # Verify token was requested
        mock_github_app.get_repository_token.assert_called_once_with(
            "test-org", "test-repo"
        )

    def test_clone_repository_command_no_token(self, mock_github_app):
        """Test clone command when no token is available."""
        mock_github_app.get_repository_token.return_value = None
        helper = GitHubAppJenkinsHelper(mock_github_app)

        clone_cmd = helper.clone_repository_command("test-org", "test-repo")

        assert clone_cmd is None

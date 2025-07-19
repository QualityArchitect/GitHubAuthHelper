from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from src.github_auth_app import GitHubApp, GitHubAppJenkinsHelper


class TestGitHubAppJenkinsHelper:
    """Test cases for GitHubAppJenkinsHelper class"""

    @pytest.fixture
    def mock_github_app(self):
        """Create a mock GitHubApp instance"""
        app = Mock(spec=GitHubApp)
        app._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        app.get_installation_token.return_value = "test_token_123456"
        return app

    def test_initialization(self, mock_github_app):
        """Test helper initialization"""
        helper = GitHubAppJenkinsHelper(mock_github_app)
        assert helper.github_app == mock_github_app

    def test_get_credentials_for_jenkins(self, mock_github_app):
        """Test getting credentials in Jenkins format"""
        helper = GitHubAppJenkinsHelper(mock_github_app)

        creds = helper.get_credentials_for_jenkins()

        assert creds["token"] == "test_token_123456"
        assert creds["token_type"] == "installation"
        assert creds["expires_at"] is not None
        assert isinstance(creds["expires_at"], str)

        # Verify token was requested
        mock_github_app.get_installation_token.assert_called_once()

    def test_get_credentials_for_jenkins_no_expiry(self, mock_github_app):
        """Test getting credentials when expiry is not set"""
        mock_github_app._token_expires_at = None
        helper = GitHubAppJenkinsHelper(mock_github_app)

        creds = helper.get_credentials_for_jenkins()

        assert creds["token"] == "test_token_123456"
        assert creds["expires_at"] is None

    def test_clone_repository_command(self, mock_github_app):
        """Test generating clone command with authentication"""
        helper = GitHubAppJenkinsHelper(mock_github_app)

        clone_cmd = helper.clone_repository_command("test-org", "test-repo")

        expected = "git clone https://x-access-token:test_token_123456@github.com/test-org/test-repo.git"
        assert clone_cmd == expected

        # Verify token was requested
        mock_github_app.get_installation_token.assert_called_once()

    def test_clone_repository_command_token_refresh(self, mock_github_app):
        """Test that clone command triggers token retrieval"""
        helper = GitHubAppJenkinsHelper(mock_github_app)

        # Get clone command multiple times
        cmd1 = helper.clone_repository_command("org1", "repo1")
        cmd2 = helper.clone_repository_command("org2", "repo2")

        # Each call should get a fresh token
        assert mock_github_app.get_installation_token.call_count == 2
        assert "x-access-token:test_token_123456" in cmd1
        assert "x-access-token:test_token_123456" in cmd2

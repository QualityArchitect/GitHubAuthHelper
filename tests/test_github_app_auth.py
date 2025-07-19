from unittest.mock import Mock, patch

import jwt
import pytest

from src.github_auth_app.app import GitHubApp
from src.github_auth_app.config import Config
from tests.fixtures.mock_responses import (
    INSTALLATION_REPOS_RESPONSE,
)


class TestGitHubApp:
    """Test cases for GitHubApp class"""

    def test_initialization(self, github_app_config):
        """Test GitHub App initialization"""
        app = GitHubApp(github_app_config)

        assert app.config.app_id == github_app_config.app_id
        assert app.config.private_key_path == github_app_config.private_key_path
        assert app.config.installation_id == github_app_config.installation_id
        assert app._private_key is None
        assert app._token_cache == {}

    def test_load_private_key(self, github_app_config):
        """Test private key loading"""
        app = GitHubApp(github_app_config)
        key = app._load_private_key()
        assert key is not None
        assert isinstance(key, bytes)
        assert b"BEGIN PRIVATE KEY" in key

    def test_load_private_key_file_not_found(self):
        """Test error handling when private key file doesn't exist"""
        config = Config(
            app_id="123",
            private_key_path="/nonexistent/path.pem",
            installation_id="456",
        )
        app = GitHubApp(config)

        with pytest.raises(FileNotFoundError):
            app._load_private_key()

    def test_create_jwt(self, github_app_config, mock_time):
        """Test JWT generation"""
        app = GitHubApp(github_app_config)
        token = app._create_jwt()

        # Decode without verification (since we're using a test key)
        decoded = jwt.decode(token, options={"verify_signature": False})

        assert decoded["iss"] == github_app_config.app_id
        assert decoded["iat"] == 1234567890
        assert decoded["exp"] == 1234567890 + 600  # 10 minutes

    def test_jwt_expiration_time(self, github_app_config):
        """Test that JWT expiration is within GitHub's limits"""
        app = GitHubApp(github_app_config)

        with patch("time.time", return_value=1234567890):
            token = app._create_jwt()
            decoded = jwt.decode(token, options={"verify_signature": False})

            # GitHub Apps JWT must expire within 10 minutes
            expiration_delta = decoded["exp"] - decoded["iat"]
            assert expiration_delta <= 600  # 10 minutes
            assert expiration_delta > 0

    def test_get_app_info(self, github_app_config, mock_requests):
        """Test getting app info"""
        app = GitHubApp(github_app_config)

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"id": 123456, "name": "Test App"}
        mock_response.raise_for_status = Mock()
        mock_requests.request.return_value = mock_response

        info = app.get_app_info()

        # Verify request
        mock_requests.request.assert_called_once()
        call_args = mock_requests.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "https://api.github.com/app"
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"].startswith("Bearer ")

        # Verify response
        assert info["id"] == 123456
        assert info["name"] == "Test App"

    def test_get_installation_id(self, github_app_config, mock_requests):
        """Test getting installation ID for a repository"""
        app = GitHubApp(github_app_config)

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = INSTALLATION_REPOS_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_requests.request.return_value = mock_response

        installation_id = app.get_installation_id("test-org", "test-repo")

        # Verify request
        mock_requests.request.assert_called_once()
        call_args = mock_requests.request.call_args
        assert "repos/test-org/test-repo/installation" in call_args[0][1]

        # Verify response
        assert installation_id == 789012

    def test_get_installation_id_not_found(self, github_app_config, mock_requests):
        """Test handling when no installation is found"""
        app = GitHubApp(github_app_config)

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_error = Mock()
        mock_error.response = mock_response
        mock_requests.request.side_effect = mock_error
        mock_requests.HTTPError = type(mock_error)

        installation_id = app.get_installation_id("test-org", "test-repo")
        assert installation_id is None

    def test_get_installation_token_success(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test successful installation token retrieval"""
        app = GitHubApp(github_app_config)

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = valid_installation_token
        mock_response.raise_for_status = Mock()
        mock_requests.request.return_value = mock_response

        token = app.get_installation_token(789012)

        # Verify request
        mock_requests.request.assert_called_once()
        call_args = mock_requests.request.call_args
        expected_url = "https://api.github.com/app/installations/789012/access_tokens"
        assert call_args[0][1] == expected_url

        # Verify token storage
        assert token == valid_installation_token["token"]
        assert "token_789012" in app._token_cache

    def test_get_installation_token_caching(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test that installation token is cached and reused"""
        app = GitHubApp(github_app_config)

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = valid_installation_token
        mock_response.raise_for_status = Mock()
        mock_requests.request.return_value = mock_response

        # Get token twice
        token1 = app.get_installation_token(789012)
        token2 = app.get_installation_token(789012)

        # Should only make one request due to caching
        assert mock_requests.request.call_count == 1
        assert token1 == token2

    def test_get_repository_token(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test getting a repository-specific token"""
        app = GitHubApp(github_app_config)

        # Mock installation lookup
        installation_response = Mock()
        installation_response.json.return_value = {"id": 789012}
        installation_response.raise_for_status = Mock()

        # Mock token response
        token_response = Mock()
        token_response.json.return_value = valid_installation_token
        token_response.raise_for_status = Mock()

        mock_requests.request.side_effect = [installation_response, token_response]

        token = app.get_repository_token("test-org", "test-repo")

        assert token == valid_installation_token["token"]
        assert mock_requests.request.call_count == 2

    def test_create_check_run(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test creating a check run"""
        app = GitHubApp(github_app_config)

        # Mock responses
        installation_response = Mock()
        installation_response.json.return_value = {"id": 789012}
        installation_response.raise_for_status = Mock()

        token_response = Mock()
        token_response.json.return_value = valid_installation_token
        token_response.raise_for_status = Mock()

        check_response = Mock()
        check_response.json.return_value = {"id": 12345, "status": "queued"}
        check_response.raise_for_status = Mock()

        mock_requests.request.side_effect = [
            installation_response,
            token_response,
            check_response,
        ]

        result = app.create_check_run(
            "test-org", "test-repo", "test-check", "abc123def"
        )

        assert result["id"] == 12345
        assert result["status"] == "queued"

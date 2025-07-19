import base64
from unittest.mock import Mock, patch

import jwt
import pytest

from github_app_auth import GitHubApp
from tests.fixtures.mock_responses import (
    CREATE_FILE_RESPONSE,
    INSTALLATIONS_RESPONSE,
    REPOSITORY_CONTENT_RESPONSE,
)


class TestGitHubApp:
    """Test cases for GitHubApp class"""

    def test_initialization(self, github_app_config):
        """Test GitHub App initialization"""
        app = GitHubApp(**github_app_config)

        assert app.app_id == github_app_config["app_id"]
        assert app.private_key_path == github_app_config["private_key_path"]
        assert app.installation_id == github_app_config["installation_id"]
        assert app._installation_token is None
        assert app._token_expires_at is None

    def test_load_private_key(self, github_app_config):
        """Test private key loading"""
        app = GitHubApp(**github_app_config)
        assert app.private_key is not None

    def test_load_private_key_file_not_found(self):
        """Test error handling when private key file doesn't exist"""
        with pytest.raises(FileNotFoundError):
            GitHubApp(
                app_id="123",
                private_key_path="/nonexistent/path.pem",
                installation_id="456",
            )

    def test_generate_jwt(self, github_app_config, mock_time):
        """Test JWT generation"""
        app = GitHubApp(**github_app_config)
        token = app.generate_jwt()

        # Decode without verification (since we're using a test key)
        decoded = jwt.decode(token, options={"verify_signature": False})

        assert decoded["iss"] == github_app_config["app_id"]
        assert decoded["iat"] == 1234567890
        assert decoded["exp"] == 1234567890 + 600  # 10 minutes

    def test_jwt_expiration_time(self, github_app_config):
        """Test that JWT expiration is within GitHub's limits"""
        app = GitHubApp(**github_app_config)

        with patch("time.time", return_value=1234567890):
            token = app.generate_jwt()
            decoded = jwt.decode(token, options={"verify_signature": False})

            # GitHub Apps JWT must expire within 10 minutes
            expiration_delta = decoded["exp"] - decoded["iat"]
            assert expiration_delta <= 600  # 10 minutes
            assert expiration_delta > 0

    def test_get_installations(self, github_app_config, mock_requests):
        """Test getting installations"""
        app = GitHubApp(**github_app_config)

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = INSTALLATIONS_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        installations = app.get_installations()

        # Verify request
        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert call_args[0][0] == "https://api.github.com/app/installations"
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"].startswith("Bearer ")

        # Verify response
        assert len(installations) == 1
        assert installations[0]["id"] == 789012
        assert installations[0]["account"]["login"] == "test-org"

    def test_get_installation_token_success(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test successful installation token retrieval"""
        app = GitHubApp(**github_app_config)

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = valid_installation_token
        mock_response.raise_for_status = Mock()
        mock_requests.post.return_value = mock_response

        token = app.get_installation_token()

        # Verify request
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        expected_url = f'https://api.github.com/app/installations/{github_app_config["installation_id"]}/access_tokens'
        assert call_args[0][0] == expected_url

        # Verify token storage
        assert token == valid_installation_token["token"]
        assert app._installation_token == token
        assert app._token_expires_at is not None

    def test_get_installation_token_no_installation_id(self, github_app_config):
        """Test error when installation ID is missing"""
        config = github_app_config.copy()
        config["installation_id"] = None
        app = GitHubApp(**config)

        with pytest.raises(ValueError, match="Installation ID is required"):
            app.get_installation_token()

    def test_get_installation_token_caching(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test that installation token is cached and reused"""
        app = GitHubApp(**github_app_config)

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = valid_installation_token
        mock_response.raise_for_status = Mock()
        mock_requests.post.return_value = mock_response

        # Get token twice
        token1 = app.get_installation_token()
        token2 = app.get_installation_token()

        # Should only make one request due to caching
        assert mock_requests.post.call_count == 1
        assert token1 == token2

    def test_get_installation_token_force_refresh(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test force refresh of installation token"""
        app = GitHubApp(**github_app_config)

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = valid_installation_token
        mock_response.raise_for_status = Mock()
        mock_requests.post.return_value = mock_response

        # Get token with and without force refresh
        token1 = app.get_installation_token()
        token2 = app.get_installation_token(force_refresh=True)

        # Should make two requests
        assert mock_requests.post.call_count == 2
        assert token1 == token2

    def test_make_api_request_success(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test successful API request"""
        app = GitHubApp(**github_app_config)

        # Mock token response
        token_response = Mock()
        token_response.json.return_value = valid_installation_token
        token_response.raise_for_status = Mock()

        # Mock API response
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = {"data": "test"}

        mock_requests.post.return_value = token_response
        mock_requests.request.return_value = api_response

        response = app.make_api_request("GET", "/test/endpoint")

        assert response.status_code == 200
        assert response.json()["data"] == "test"

    def test_make_api_request_token_refresh_on_401(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test automatic token refresh on 401 response"""
        app = GitHubApp(**github_app_config)

        # Mock token response
        token_response = Mock()
        token_response.json.return_value = valid_installation_token
        token_response.raise_for_status = Mock()
        mock_requests.post.return_value = token_response

        # Mock API responses - first 401, then 200
        api_response_401 = Mock()
        api_response_401.status_code = 401

        api_response_200 = Mock()
        api_response_200.status_code = 200
        api_response_200.json.return_value = {"data": "success"}

        mock_requests.request.side_effect = [api_response_401, api_response_200]

        response = app.make_api_request("GET", "/test/endpoint")

        # Should make 2 API requests and 2 token requests
        assert mock_requests.request.call_count == 2
        assert mock_requests.post.call_count == 2  # Initial + refresh
        assert response.status_code == 200

    def test_get_repository_content(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test getting repository content"""
        app = GitHubApp(**github_app_config)

        # Setup mocks
        token_response = Mock()
        token_response.json.return_value = valid_installation_token
        token_response.raise_for_status = Mock()
        mock_requests.post.return_value = token_response

        content_response = Mock()
        content_response.status_code = 200
        content_response.json.return_value = REPOSITORY_CONTENT_RESPONSE
        content_response.raise_for_status = Mock()
        mock_requests.request.return_value = content_response

        content = app.get_repository_content("test-org", "test-repo", "README.md")

        assert content["name"] == "README.md"
        assert content["sha"] == "abc123def456"
        assert base64.b64decode(content["content"]).decode() == "Hello World!"

    def test_create_or_update_file(
        self, github_app_config, mock_requests, valid_installation_token
    ):
        """Test creating or updating a file"""
        app = GitHubApp(**github_app_config)

        # Setup mocks
        token_response = Mock()
        token_response.json.return_value = valid_installation_token
        token_response.raise_for_status = Mock()
        mock_requests.post.return_value = token_response

        create_response = Mock()
        create_response.status_code = 201
        create_response.json.return_value = CREATE_FILE_RESPONSE
        create_response.raise_for_status = Mock()
        mock_requests.request.return_value = create_response

        result = app.create_or_update_file(
            owner="test-org",
            repo="test-repo",
            path="test-file.txt",
            content="Hello from GitHub App!",
            message="Test commit from GitHub App",
        )

        # Verify request
        call_args = mock_requests.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/repos/test-org/test-repo/contents/test-file.txt" in call_args[0][1]

        # Verify request body
        request_data = call_args[1]["json"]
        assert request_data["message"] == "Test commit from GitHub App"
        assert (
            base64.b64decode(request_data["content"]).decode()
            == "Hello from GitHub App!"
        )

        # Verify response
        assert result["content"]["path"] == "test-file.txt"
        assert result["commit"]["message"] == "Test commit from GitHub App"

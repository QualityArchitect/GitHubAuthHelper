import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest


class TestJenkinsCLI:
    """Test cases for Jenkins CLI script."""

    @pytest.fixture
    def mock_config(self):
        """Mock the Config class."""
        with patch("src.github_auth_app.jenkins_helper.Config") as mock:
            config_instance = Mock()
            config_instance.app_id = "123456"
            config_instance.private_key_path = "/path/to/key.pem"
            config_instance.installation_id = None
            mock.return_value = config_instance
            yield mock

    @pytest.fixture
    def mock_github_app_class(self):
        """Mock the GitHubApp class."""
        with patch("src.github_auth_app.jenkins_helper.GitHubApp") as mock:
            yield mock

    def test_cli_token_output(self, mock_config, mock_github_app_class, capsys):
        """Test CLI with token output format."""
        # Set up mock
        app_instance = Mock()
        app_instance.get_repository_token.return_value = "test_cli_token_123"
        mock_github_app_class.return_value = app_instance

        test_args = [
            "github-app-auth",
            "test-org",
            "test-repo",
            "--output-format",
            "token",
        ]

        with patch("sys.argv", test_args):
            from src.github_auth_app.jenkins_helper import main

            main()

        captured = capsys.readouterr()
        assert captured.out.strip() == "test_cli_token_123"
        assert captured.err == ""

        # Verify methods were called
        app_instance.get_repository_token.assert_called_once_with(
            "test-org", "test-repo"
        )

    def test_cli_json_output(self, mock_config, mock_github_app_class, capsys):
        """Test CLI with JSON output format."""
        # Set up mock
        app_instance = Mock()
        app_instance.get_repository_token.return_value = "test_cli_token_123"
        app_instance.get_installation_id.return_value = 12345
        app_instance._token_cache = {
            "token_12345": {
                "token": "test_cli_token_123",
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            }
        }
        mock_github_app_class.return_value = app_instance

        test_args = [
            "github-app-auth",
            "test-org",
            "test-repo",
            "--output-format",
            "json",
        ]

        with patch("sys.argv", test_args):
            from src.github_auth_app.jenkins_helper import main

            main()

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["token"] == "test_cli_token_123"
        assert output["token_type"] == "installation"
        assert "expires_at" in output

    def test_cli_env_output(self, mock_config, mock_github_app_class, capsys):
        """Test CLI with env output format."""
        # Set up mock
        app_instance = Mock()
        app_instance.get_repository_token.return_value = "test_cli_token_123"
        mock_github_app_class.return_value = app_instance

        test_args = [
            "github-app-auth",
            "test-org",
            "test-repo",
            "--output-format",
            "env",
        ]

        with patch("sys.argv", test_args):
            from src.github_auth_app.jenkins_helper import main

            main()

        captured = capsys.readouterr()
        assert captured.out.strip() == "GITHUB_TOKEN=test_cli_token_123"

    def test_cli_clone_output(self, mock_config, mock_github_app_class, capsys):
        """Test CLI with clone output format."""
        # Set up mock
        app_instance = Mock()
        app_instance.get_repository_token.return_value = "test_cli_token_123"
        mock_github_app_class.return_value = app_instance

        test_args = [
            "github-app-auth",
            "test-org",
            "test-repo",
            "--output-format",
            "clone",
        ]

        with patch("sys.argv", test_args):
            from src.github_auth_app.jenkins_helper import main

            main()

        captured = capsys.readouterr()
        expected = "git clone https://x-access-token:test_cli_token_123@github.com/test-org/test-repo.git"
        assert captured.out.strip() == expected

    def test_cli_no_token_error(self, mock_config, mock_github_app_class, capsys):
        """Test CLI error when no token is available."""
        # Set up mock
        app_instance = Mock()
        app_instance.get_repository_token.return_value = None
        mock_github_app_class.return_value = app_instance

        test_args = [
            "github-app-auth",
            "test-org",
            "test-repo",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                from src.github_auth_app.jenkins_helper import main

                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "No installation found" in captured.err

    def test_cli_missing_args(self, capsys):
        """Test CLI with missing required arguments."""
        test_args = ["github-app-auth"]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                from src.github_auth_app.jenkins_helper import main

                main()

            assert exc_info.value.code == 2  # argparse exit code

    def test_cli_help(self, capsys):
        """Test CLI help output."""
        test_args = ["github-app-auth", "--help"]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                from src.github_auth_app.jenkins_helper import main

                main()

            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "GitHub App authentication helper" in captured.out
        assert "owner" in captured.out
        assert "repo" in captured.out
        assert "--output-format" in captured.out

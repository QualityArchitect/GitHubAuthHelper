import json
import sys
from unittest.mock import Mock, patch

import pytest

from jenkins_github_app_auth import main


class TestJenkinsCLI:
    """Test cases for Jenkins CLI script"""

    @pytest.fixture
    def mock_github_app_class(self):
        """Mock the GitHubApp class"""
        with patch("jenkins_github_app_auth.GitHubApp") as mock:
            instance = Mock()
            instance.get_installation_token.return_value = "test_cli_token_123"
            instance._token_expires_at = None
            mock.return_value = instance
            yield mock

    def test_cli_token_output(self, mock_github_app_class, capsys):
        """Test CLI with token output format"""
        test_args = [
            "jenkins_github_app_auth.py",
            "--app-id",
            "123456",
            "--private-key-path",
            "/path/to/key.pem",
            "--installation-id",
            "789012",
            "--output-format",
            "token",
        ]

        with patch.object(sys, "argv", test_args):
            main()

        captured = capsys.readouterr()
        assert captured.out.strip() == "test_cli_token_123"
        assert captured.err == ""

        # Verify GitHubApp was initialized correctly
        mock_github_app_class.assert_called_once_with(
            app_id="123456",
            private_key_path="/path/to/key.pem",
            installation_id="789012",
        )

    def test_cli_json_output(self, mock_github_app_class, capsys):
        """Test CLI with JSON output format"""
        # Set up mock with expiration time
        instance = mock_github_app_class.return_value
        instance._token_expires_at = Mock()
        instance._token_expires_at.isoformat.return_value = "2024-01-01T12:00:00"

        test_args = [
            "jenkins_github_app_auth.py",
            "--app-id",
            "123456",
            "--private-key-path",
            "/path/to/key.pem",
            "--installation-id",
            "789012",
            "--output-format",
            "json",
        ]

        with patch.object(sys, "argv", test_args):
            main()

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["token"] == "test_cli_token_123"
        assert output["expires_at"] == "2024-01-01T12:00:00"

    def test_cli_export_output(self, mock_github_app_class, capsys):
        """Test CLI with export output format"""
        test_args = [
            "jenkins_github_app_auth.py",
            "--app-id",
            "123456",
            "--private-key-path",
            "/path/to/key.pem",
            "--installation-id",
            "789012",
            "--output-format",
            "export",
        ]

        with patch.object(sys, "argv", test_args):
            main()

        captured = capsys.readouterr()
        assert captured.out.strip() == 'export GITHUB_TOKEN="test_cli_token_123"'

    def test_cli_missing_required_args(self, capsys):
        """Test CLI with missing required arguments"""
        test_args = ["jenkins_github_app_auth.py"]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 2  # argparse exit code for missing args

    def test_cli_error_handling(self, mock_github_app_class, capsys):
        """Test CLI error handling"""
        # Make the token retrieval fail
        instance = mock_github_app_class.return_value
        instance.get_installation_token.side_effect = Exception("API Error")

        test_args = [
            "jenkins_github_app_auth.py",
            "--app-id",
            "123456",
            "--private-key-path",
            "/path/to/key.pem",
            "--installation-id",
            "789012",
        ]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error: API Error" in captured.err

    def test_cli_help(self, capsys):
        """Test CLI help output"""
        test_args = ["jenkins_github_app_auth.py", "--help"]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "Get GitHub App token for Jenkins" in captured.out
        assert "--app-id" in captured.out
        assert "--private-key-path" in captured.out
        assert "--installation-id" in captured.out
        assert "--output-format" in captured.out

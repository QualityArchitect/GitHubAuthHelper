import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.github_auth_app.config import Config


@pytest.fixture
def mock_private_key():
    """Generate a test RSA private key"""
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    return private_key


@pytest.fixture
def private_key_file(mock_private_key):
    """Create a temporary private key file"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pem") as f:
        pem = mock_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        f.write(pem)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def github_app_config(private_key_file):
    """Basic GitHub App configuration"""
    return Config(
        app_id="123456",
        private_key_path=private_key_file,
        installation_id="789012",
    )


@pytest.fixture
def mock_time():
    """Mock time for consistent testing"""
    with patch("time.time") as mock:
        mock.return_value = 1234567890  # Fixed timestamp
        yield mock


@pytest.fixture
def mock_requests():
    """Mock requests library"""
    with patch("src.github_auth_app.app.requests") as mock:
        yield mock


@pytest.fixture
def valid_installation_token():
    """Generate a valid installation token response"""
    # Use timezone-aware datetime
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    return {
        "token": "ghs_test_installation_token_123456789",
        "expires_at": expires_at.isoformat().replace(
            "+00:00", "Z"
        ),  # GitHub uses 'Z' suffix
        "permissions": {"contents": "write", "metadata": "read"},
    }

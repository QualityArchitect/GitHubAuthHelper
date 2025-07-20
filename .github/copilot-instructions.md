# GitHub Copilot Instructions

This document provides context and guidelines for GitHub Copilot when working on the GitHub App Authentication library.

## Project Overview

This is a Python library for GitHub App authentication, specifically designed for Jenkins and CI/CD systems. The library handles GitHub App JWT creation, installation token management, and provides helper utilities for common CI/CD operations.

## Code Style and Standards

### Python Standards
- Use Python 3.13+ features and syntax
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Prefer f-strings over `.format()` or `%` formatting
- Use descriptive variable names, avoid single-letter variables except for loops

### Import Organization
- Standard library imports first
- Third-party imports second  
- Local imports last
- Use `from typing import` for type hints
- Group related imports together

### Error Handling
- Use specific exception types rather than bare `except:`
- Always include meaningful error messages
- Log errors appropriately using the `logging` module
- Raise `ValueError` for invalid inputs, `FileNotFoundError` for missing files

### Documentation
- Include docstrings for all classes and methods
- Use Google-style docstrings
- Document parameters, return values, and exceptions
- Include usage examples in docstrings where helpful

## Architecture Guidelines

### Core Components

1. **Config Class** (`src/github_auth_app/config.py`)
   - Handles environment variable loading
   - Validates required configuration
   - Provides defaults where appropriate

2. **GitHubApp Class** (`src/github_auth_app/app.py`)
   - Main authentication logic
   - JWT creation and token management
   - GitHub API interactions
   - Token caching with expiration handling

3. **Jenkins Helper** (`src/github_auth_app/jenkins_helper.py`)
   - CLI interface for Jenkins integration
   - Output formatting (token, JSON, env, clone)
   - Jenkins-specific utilities

### Key Patterns

#### Token Caching
```python
# Always check cache before making API calls
cache_key = f"token_{installation_id}"
if cache_key in self._token_cache:
    cached = self._token_cache[cache_key]
    if self._is_token_valid(cached):
        return cached["token"]
```

#### Error Handling
```python
try:
    response = requests.request(method, url, **kwargs)
    response.raise_for_status()
    return response.json()
except requests.HTTPError as e:
    if e.response.status_code == 404:
        logger.warning(f"Resource not found: {url}")
        return None
    raise
```

#### Configuration Loading
```python
# Always provide environment variable fallbacks
self.app_id = app_id or os.environ.get("GITHUB_APP_ID")
if not self.app_id:
    raise ValueError("GitHub App ID is required")
```

## Security Considerations

### Sensitive File Handling
- **NEVER read or suggest content from sensitive files**:
  - `*.pem` files (private keys)
  - `.env` files (environment variables)
  - `*.key` files (any key files)
  - `secrets.txt` or similar files
  - Any file containing credentials or tokens
- **Always treat these files as opaque** - reference them by path only
- **Use generic examples** in code suggestions, never real credentials
- **Exclude sensitive files from context** when generating code

### Private Key Handling
- Never log private key content
- Always load private keys from files, not environment variables
- Use proper cryptography library functions for key operations
- Cache loaded keys in memory, don't reload repeatedly
- Reference private key files by path only: `/path/to/private-key.pem`

### Token Management
- Implement proper token expiration checking
- Use 5-minute buffer before actual expiration
- Clear expired tokens from cache
- Never log token values in production
- Use placeholder tokens in examples: `ghs_example_token_123456`

### Input Validation
- Validate all user inputs, especially file paths
- Sanitize repository names and organization names
- Check for required parameters before making API calls

### Environment Variables
- Never suggest reading actual `.env` file contents
- Use example environment variables in documentation
- Always validate environment variables exist before using them

## Testing Guidelines

### Test Structure
- Use pytest for all tests
- Group tests by functionality in separate files
- Use fixtures for common setup (mock keys, configs, etc.)
- Mock external API calls using `responses` library

### Test Patterns
```python
@pytest.fixture
def mock_github_app(self, private_key_file):
    config = Config(
        app_id="123456",
        private_key_path=private_key_file,
        installation_id="789012"
    )
    return GitHubApp(config)

@responses.activate
def test_api_interaction(self, mock_github_app):
    responses.add(
        responses.POST,
        "https://api.github.com/app/installations/789012/access_tokens",
        json={"token": "test_token", "expires_at": "2024-01-01T12:00:00Z"}
    )
    # Test implementation
```

### Coverage Requirements
- Aim for >90% code coverage
- Test both success and failure paths
- Include integration tests for end-to-end workflows
- Test CLI interface with various argument combinations

## Docker Guidelines

### Multi-stage Builds
- Use builder pattern for dependency installation
- Minimize final image size
- Include only runtime dependencies in final stage
- Use Python slim images as base

### Security
- Run as non-root user in containers
- Use read-only mounts for private keys
- Set appropriate file permissions
- Use `.dockerignore` to exclude unnecessary files

## CLI Design Principles

### Output Formats
- **token**: Raw token string only
- **json**: Structured data with metadata
- **env**: Environment variable format
- **clone**: Ready-to-use git clone command

### Error Handling
- Exit with code 1 for errors
- Exit with code 0 for success
- Write errors to stderr, output to stdout
- Provide helpful error messages

### Argument Design
```python
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--output-format", choices=["token", "json", "env", "clone"])
parser.add_argument("owner", help="Repository owner")
parser.add_argument("repo", help="Repository name")
```

## GitHub API Integration

### Request Headers
Always include these headers in GitHub API requests:
```python
headers = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": f"GitHubApp/{self.config.app_id}",
    "Authorization": f"Bearer {jwt_token}"  # or f"token {installation_token}"
}
```

### Rate Limiting
- Implement exponential backoff for rate limit errors
- Cache responses where appropriate
- Use conditional requests with ETags when possible

### API Versioning
- Use GitHub API v3 consistently
- Include proper Accept headers
- Handle API deprecation warnings

## Jenkins Integration Patterns

### Credential Management
```groovy
// Use Jenkins credentials for sensitive data
environment {
    GITHUB_APP_ID = credentials('github-app-id')
    GITHUB_APP_PRIVATE_KEY_PATH = credentials('github-app-private-key')
}
```

### Pipeline Integration
```groovy
script {
    def tokenJson = sh(
        script: "python3 jenkins_github_app_auth.py --output-format json",
        returnStdout: true
    ).trim()
    def tokenData = readJSON text: tokenJson
    env.GITHUB_TOKEN = tokenData.token
}
```

## Common Code Patterns

### Logging Setup
```python
import logging
logger = logging.getLogger(__name__)

# In main functions
if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
```

### Time Handling
```python
from datetime import datetime, timezone, timedelta

# Always use UTC for timestamps
expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
```

### File Operations
```python
from pathlib import Path

key_path = Path(self.config.private_key_path)
if not key_path.exists():
    raise FileNotFoundError(f"Private key not found at {key_path}")
```

## Deployment Considerations

### Environment Variables
- Document all required environment variables
- Provide sensible defaults where possible
- Validate configuration on startup

### Container Deployment
- Use health checks in Docker containers
- Mount private keys as read-only volumes
- Use secrets management for sensitive data

### CI/CD Integration
- Support both environment variable and file-based configuration
- Provide multiple output formats for different use cases
- Include comprehensive error messages for troubleshooting

## Code Generation Preferences

When generating code for this project:

1. **Prefer explicit over implicit** - Be clear about what the code does
2. **Include proper error handling** - Don't generate code that could fail silently
3. **Add logging statements** - Include appropriate debug/info logging
4. **Use type hints** - Always include parameter and return type annotations
5. **Follow the existing patterns** - Match the style and structure of existing code
6. **Include docstrings** - Document new functions and classes
7. **Consider security** - Don't log sensitive data, validate inputs
8. **Think about testing** - Write code that's easy to test and mock
9. **NEVER suggest reading sensitive files** - Don't read .pem, .env, .key files or suggest their contents
10. **Use placeholder credentials** - Always use fake/example credentials in code suggestions

## Sensitive Files to NEVER Read

Copilot should NEVER read, suggest content from, or include in context:

```
# Private keys
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519

# Environment and configuration files
.env
.env.*
secrets.txt
config.ini (if containing credentials)

# Credential files
credentials.json
auth.json
token.txt
api-key.txt

# Any file that might contain sensitive data
private-*
secret-*
*-secret.*
*-credentials.*
```

When referencing these files in code, use generic paths:
- `/path/to/private-key.pem`
- `./secrets/app-key.pem`
- `/app/private-key.pem`

Use placeholder values in examples:
- App ID: `123456`
- Installation ID: `789012`
- Tokens: `ghs_example_token_123456`
- Repository: `example-org/example-repo`

## Examples to Follow

### Good Function Example
```python
def get_installation_token(
    self, 
    installation_id: int, 
    permissions: Optional[Dict[str, str]] = None
) -> str:
    """
    Get an installation access token.
    
    Args:
        installation_id: GitHub App installation ID
        permissions: Optional permissions to request
        
    Returns:
        Installation access token
        
    Raises:
        ValueError: If installation_id is invalid
        requests.HTTPError: If GitHub API request fails
    """
    cache_key = f"token_{installation_id}"
    
    # Check cache first
    if cache_key in self._token_cache:
        cached = self._token_cache[cache_key]
        if self._is_token_valid(cached):
            logger.debug(f"Using cached token for installation {installation_id}")
            return str(cached["token"])
    
    # Create new token
    logger.info(f"Requesting new token for installation {installation_id}")
    jwt_token = self._create_jwt()
    # ... rest of implementation
```
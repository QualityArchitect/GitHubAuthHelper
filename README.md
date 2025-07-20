# GitHub App Authentication

A Python library for GitHub App authentication, designed for Jenkins and other CI/CD systems.

## Features

- **GitHub App Authentication**: Generate installation tokens using GitHub App credentials
- **Token Caching**: Automatic token caching and refresh handling
- **Jenkins Integration**: CLI tool and helper classes specifically designed for Jenkins pipelines
- **Docker Support**: Ready-to-use Docker containers for easy deployment
- **Repository Operations**: Create check runs, deployments, and manage repository access
- **Multiple Output Formats**: Support for token, JSON, environment variable, and git clone command outputs

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/QualityArchitect/GitHubAuthHelper.git
cd github-auth-app

# Install with pip (development mode)
pip install -e .

# Or install with uv (faster)
uv pip install -e .
```

### Using Docker

```bash
# Clone the repository first
git clone https://github.com/QualityArchitect/GitHubAuthHelper.git
cd github-auth-app

# Build the Docker image
docker build -t github-app-auth .
```

### Direct Script Usage

You can also use the `jenkins_github_app_auth.py` script directly without installation:

```bash
python3 jenkins_github_app_auth.py \
    --app-id YOUR_APP_ID \
    --private-key-path /path/to/private-key.pem \
    --installation-id YOUR_INSTALLATION_ID \
    --output-format token
```

## Quick Start

### Environment Variables

Set the following environment variables:

```bash
export GITHUB_APP_ID="your-app-id"
export GITHUB_APP_PRIVATE_KEY_PATH="/path/to/private-key.pem"
export GITHUB_APP_INSTALLATION_ID="your-installation-id"
```

### Basic Usage

```python
from github_auth_app import GitHubApp
from github_auth_app.config import Config

# Initialize with environment variables
config = Config()
app = GitHubApp(config)

# Get installation token
token = app.get_installation_token(installation_id)

# Get repository-specific token
repo_token = app.get_repository_token("owner", "repo")
```

## Jenkins Integration

### Using the CLI Tool

After installing from source, you can use the command-line interface:

```bash
# Get token for a repository
github-app-auth owner repo --output-format token

# Get JSON format with expiration info
github-app-auth owner repo --output-format json

# Get environment variable format
github-app-auth owner repo --output-format env

# Get git clone command with embedded token
github-app-auth owner repo --output-format clone
```

Or use the script directly:

```bash
# Using the direct script
python3 src/github_auth_app/jenkins_helper.py owner repo --output-format token

# Using the Jenkins-specific script
python3 jenkins_github_app_auth.py \
    --app-id YOUR_APP_ID \
    --private-key-path /path/to/private-key.pem \
    --installation-id YOUR_INSTALLATION_ID \
    --output-format token
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        GITHUB_APP_ID = credentials('github-app-id')
        GITHUB_APP_PRIVATE_KEY_PATH = credentials('github-app-private-key')
        GITHUB_APP_INSTALLATION_ID = credentials('github-app-installation-id')
    }
    
    stages {
        stage('Get GitHub Token') {
            steps {
                script {
                    // Get GitHub App token
                    def tokenJson = sh(
                        script: """
                            python3 jenkins_github_app_auth.py \
                                --app-id ${GITHUB_APP_ID} \
                                --private-key-path ${GITHUB_APP_PRIVATE_KEY_PATH} \
                                --installation-id ${GITHUB_APP_INSTALLATION_ID} \
                                --output-format json
                        """,
                        returnStdout: true
                    ).trim()
                    
                    def tokenData = readJSON text: tokenJson
                    
                    // Use token for git operations
                    withEnv(["GITHUB_TOKEN=${tokenData.token}"]) {
                        sh '''
                            git config --global url."https://x-access-token:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"
                            git clone https://github.com/your-org/your-repo.git
                        '''
                    }
                }
            }
        }
    }
}
```

### Using Docker in Jenkins

```groovy
pipeline {
    agent any
    
    stages {
        stage('Authenticate with GitHub') {
            steps {
                script {
                    def token = sh(
                        script: """
                            docker run --rm \
                                -v ${WORKSPACE}/private-key.pem:/app/private-key.pem:ro \
                                -e GITHUB_APP_ID=${GITHUB_APP_ID} \
                                -e GITHUB_APP_INSTALLATION_ID=${GITHUB_APP_INSTALLATION_ID} \
                                github-app-auth:latest \
                                --app-id ${GITHUB_APP_ID} \
                                --private-key-path /app/private-key.pem \
                                --installation-id ${GITHUB_APP_INSTALLATION_ID} \
                                --output-format token
                        """,
                        returnStdout: true
                    ).trim()
                    
                    env.GITHUB_TOKEN = token
                }
            }
        }
    }
}
```

## API Reference

### GitHubApp Class

```python
from github_auth_app import GitHubApp
from github_auth_app.config import Config

config = Config(
    app_id="123456",
    private_key_path="/path/to/key.pem",
    installation_id="789012"
)
app = GitHubApp(config)
```

#### Methods

- `get_app_info()` - Get GitHub App information
- `get_installation_id(owner, repo)` - Get installation ID for a repository
- `get_installation_token(installation_id)` - Get installation access token
- `get_repository_token(owner, repo)` - Get token for specific repository
- `create_check_run(owner, repo, name, head_sha, **kwargs)` - Create a check run
- `update_check_run(owner, repo, check_run_id, **kwargs)` - Update a check run
- `create_deployment(owner, repo, ref, environment, **kwargs)` - Create deployment
- `create_deployment_status(owner, repo, deployment_id, state, **kwargs)` - Update deployment status

### GitHubAppJenkinsHelper Class

```python
from github_auth_app.jenkins_helper import GitHubAppJenkinsHelper

helper = GitHubAppJenkinsHelper(github_app)

# Get credentials for Jenkins
creds = helper.get_credentials_for_jenkins("owner", "repo")

# Generate clone command
clone_cmd = helper.clone_repository_command("owner", "repo")
```

## Configuration

### Config Class

The `Config` class handles configuration from environment variables or direct parameters:

```python
from github_auth_app.config import Config

# From environment variables
config = Config.from_env()

# Direct configuration
config = Config(
    app_id="123456",
    private_key_path="/path/to/private-key.pem",
    installation_id="789012"
)
```

### Required Environment Variables

- `GITHUB_APP_ID` - Your GitHub App ID
- `GITHUB_APP_PRIVATE_KEY_PATH` - Path to your private key file
- `GITHUB_APP_INSTALLATION_ID` - Installation ID (optional, can be discovered automatically)

## Docker Usage

### Building the Image

```bash
# Production image
make build

# Development image with testing tools
docker build -f dev.Dockerfile -t github-app-auth:dev .
```

### Running with Docker Compose

```bash
# Get help
docker-compose run --rm github-app-auth --help

# Get token
docker-compose run --rm github-app-auth \
    --app-id $GITHUB_APP_ID \
    --private-key-path /app/private-key.pem \
    --installation-id $GITHUB_APP_INSTALLATION_ID \
    --output-format json
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/QualityArchitect/GitHubAuthHelper.git
cd github-auth-app

# Install in development mode
pip install -e ".[dev]"

# Or using uv (recommended)
uv pip install -e ".[dev]"

# Build development environment with Docker
make dev

# Run tests
make test
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/github_auth_app --cov-report=html

# Run integration tests
pytest -m integration
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## GitHub App Setup

1. **Create a GitHub App** in your organization or personal account
2. **Generate a private key** and save it securely
3. **Install the app** on repositories you want to access
4. **Grant appropriate permissions**:
   - Contents: Read/Write (for repository access)
   - Metadata: Read (for basic repository info)
   - Checks: Write (for creating check runs)
   - Deployments: Write (for deployment management)

## Security Considerations

- **Store private keys securely** Never commit private keys to version control
- **Use environment variables** for sensitive configuration
- **Rotate tokens regularly** The library handles token expiration automatically
- **Limit app permissions** Only grant the minimum permissions required
- **Use installation tokens** They're scoped to specific repositories and have limited lifetime

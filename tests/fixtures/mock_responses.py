"""Mock API responses for testing"""

INSTALLATIONS_RESPONSE = [
    {
        "id": 789012,
        "account": {"login": "test-org", "id": 12345, "type": "Organization"},
        "repository_selection": "all",
        "access_tokens_url": "https://api.github.com/app/installations/789012/access_tokens",
        "repositories_url": "https://api.github.com/installation/repositories",
    }
]

REPOSITORY_CONTENT_RESPONSE = {
    "name": "README.md",
    "path": "README.md",
    "sha": "abc123def456",
    "size": 1234,
    "url": "https://api.github.com/repos/test-org/test-repo/contents/README.md",
    "type": "file",
    "content": "SGVsbG8gV29ybGQh",  # Base64 encoded "Hello World!"
    "encoding": "base64",
}

CREATE_FILE_RESPONSE = {
    "content": {
        "name": "test-file.txt",
        "path": "test-file.txt",
        "sha": "new123sha456",
        "size": 20,
        "url": "https://api.github.com/repos/test-org/test-repo/contents/test-file.txt",
    },
    "commit": {"sha": "commit123abc", "message": "Test commit from GitHub App"},
}

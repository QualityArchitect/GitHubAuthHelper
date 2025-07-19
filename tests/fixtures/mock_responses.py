"""Mock responses for GitHub API testing."""

INSTALLATIONS_RESPONSE = [
    {
        "id": 789012,
        "account": {
            "login": "test-org",
            "id": 12345,
            "type": "Organization",
        },
        "repository_selection": "all",
        "access_tokens_url": "https://api.github.com/app/installations/789012/access_tokens",
        "repositories_url": "https://api.github.com/installation/repositories",
    }
]

REPOSITORY_CONTENT_RESPONSE = {
    "type": "file",
    "encoding": "base64",
    "size": 12,
    "name": "README.md",
    "path": "README.md",
    "content": "SGVsbG8gV29ybGQh",  # "Hello World!" in base64
    "sha": "abc123def456",
    "url": "https://api.github.com/repos/test-org/test-repo/contents/README.md",
    "git_url": "https://api.github.com/repos/test-org/test-repo/git/blobs/abc123def456",
    "html_url": "https://github.com/test-org/test-repo/blob/master/README.md",
    "download_url": "https://raw.githubusercontent.com/test-org/test-repo/master/README.md",
}

CREATE_FILE_RESPONSE = {
    "content": {
        "name": "test-file.txt",
        "path": "test-file.txt",
        "sha": "def789ghi012",
        "size": 22,
        "url": "https://api.github.com/repos/test-org/test-repo/contents/test-file.txt",
        "html_url": "https://github.com/test-org/test-repo/blob/master/test-file.txt",
        "git_url": "https://api.github.com/repos/test-org/test-repo/git/blobs/def789ghi012",
        "type": "file",
    },
    "commit": {
        "sha": "7638417db6d59f3c431d3e1f261cc637155684cd",
        "url": "https://api.github.com/repos/test-org/test-repo/git/commits/7638417db6d59f3c431d3e1f261cc637155684cd",
        "html_url": "https://github.com/test-org/test-repo/commit/7638417db6d59f3c431d3e1f261cc637155684cd",
        "message": "Test commit from GitHub App",
        "tree": {
            "url": "https://api.github.com/repos/test-org/test-repo/git/trees/691272480426f78a0138979dd3ce63b77f706feb",
            "sha": "691272480426f78a0138979dd3ce63b77f706feb",
        },
    },
}

INSTALLATION_REPOS_RESPONSE = {
    "id": 789012,
    "account": {
        "login": "test-org",
        "id": 12345,
        "type": "Organization",
    },
}

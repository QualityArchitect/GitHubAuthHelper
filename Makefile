.PHONY: help build run test dev clean

help:
	@echo "Available commands:"
	@echo "  make build    - Build the Docker image"
	@echo "  make run      - Run the GitHub App auth tool"
	@echo "  make test     - Run tests"
	@echo "  make dev      - Start development environment"
	@echo "  make clean    - Clean up containers and images"

build:
	docker build -f Dockerfile -t github-app-auth:slim .

run:
	docker run --rm \
		-v $(PWD)/private-key.pem:/app/private-key.pem:ro \
		-e GITHUB_APP_ID=$(GITHUB_APP_ID) \
		-e GITHUB_APP_INSTALLATION_ID=$(GITHUB_APP_INSTALLATION_ID) \
		github-app-auth:latest \
		--app-id $(GITHUB_APP_ID) \
		--private-key-path /app/private-key.pem \
		--installation-id $(GITHUB_APP_INSTALLATION_ID) \
		--output-format json

test:
	docker-compose run --rm dev python -m pytest -v

dev:
	docker-compose run --rm dev

clean:
	docker-compose down
	docker rmi github-app-auth:latest github-app-auth:slim || true

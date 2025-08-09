# Zola Makefile

# Variables
ZOLA := zola
SRC_DIR := public
TARGET_HOST := karan@$(SERVER_IP)
TARGET_DIR := /home/karan/mrkaran-dev/public

# Default target
all: build

# Check if SERVER_IP is set
check-env:
ifndef SERVER_IP
	$(error SERVER_IP is undefined. Use `make deploy SERVER_IP=your.ip.here` or export it as environment variable.)
endif

# Serve the site using zola
preview:
	$(ZOLA) serve

# Build the site using zola
build:
	$(ZOLA) build

# Deploy the site using rsync
deploy: check-env build
	rsync -avz --delete $(SRC_DIR)/ $(TARGET_HOST):$(TARGET_DIR)

# Git commit and push
push:
	git add --all
	git commit -m "automated push"
	git push origin main

# Update project metadata from GitHub
projects:
	@echo "Fetching latest project metadata from GitHub..."
	@uv run scripts/fetch_all_github_projects.py mr-karan > content/projects/data.toml
	@echo "Successfully updated content/projects/data.toml"

.PHONY: build deploy check-env push projects

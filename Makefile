# Zola Makefile

# Variables
ZOLA := zola
SRC_DIR := public
TARGET_HOST := karan@$(SERVER_IP)
TARGET_DIR := /home/karan/website/public

# Default target
all: build

# Check if SERVER_IP is set
check-env:
ifndef SERVER_IP
	$(error SERVER_IP is undefined. Use `make deploy SERVER_IP=your.ip.here` or export it as environment variable.)
endif

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

.PHONY: build deploy check-env push

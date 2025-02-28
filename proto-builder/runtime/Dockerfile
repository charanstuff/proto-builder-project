# Dockerfile
FROM python:3.9-slim

RUN echo "Dockerfile: Building..."

# Install Node.js, npm and dependencies
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get install -y nodejs npm && \
    rm -rf /var/lib/apt/lists/*

RUN echo "Dockerfile: Done..."

WORKDIR /code

#!/bin/bash

# AI Shorts Factory - Deployment Script
# Run this on your Linux (WSL) server to pull the latest image and restart the container.

set -e # Exit immediately if a command exits with a non-zero status

IMAGE="ghcr.io/devendramandlik30-del/ai-shorts-factory:latest"
CONTAINER_NAME="shorts-factory-prod"

echo "🔄 Pulling latest image from GHCR..."
docker pull $IMAGE

echo "🛑 Stopping old container (if running)..."
docker rm -f $CONTAINER_NAME 2>/dev/null || true

echo "🚀 Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  --env-file .env \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/credentials:/app/credentials" \
  -v "$(pwd)/topics.txt:/app/topics.txt" \
  --restart unless-stopped \
  $IMAGE python daily_run.py

echo "✅ Deployment complete! Container is running in the background."
echo "To view logs, run: docker logs -f $CONTAINER_NAME"
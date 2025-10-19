#!/bin/bash

# Start MongoDB using Docker Compose
# This script starts the MongoDB container and waits for it to be ready

set -e

echo "Starting MongoDB with Docker Compose..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start MongoDB container
docker-compose up -d mongodb

echo "Waiting for MongoDB to be ready..."

# Wait for MongoDB to be healthy
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        echo "MongoDB is ready!"
        echo "MongoDB is running on mongodb://localhost:27017"
        echo "Mongo Express (GUI) is available at http://localhost:8081"
        exit 0
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "Error: MongoDB failed to start within the timeout period"
echo "Check logs with: docker-compose logs mongodb"
exit 1

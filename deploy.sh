#!/bin/bash

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Stop any running containers
echo "Stopping existing containers..."
docker-compose down

# Build and start the containers
echo "Building and starting containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "gomoku-server"; then
    echo "Server is running!"
    echo "Server URL: http://localhost:8000"
    echo "WebSocket URL: ws://localhost:8000/ws"
    echo ""
    echo "To test the server:"
    echo "1. Single Player: Open the game and select 'Single Player'"
    echo "2. Multiplayer: "
    echo "   - First player: Select 'Host Game'"
    echo "   - Second player: Select 'Join Game' and enter the code"
    echo ""
    echo "To view logs: docker-compose logs -f"
else
    echo "Error: Server failed to start!"
    docker-compose logs
    exit 1
fi

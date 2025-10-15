#!/bin/bash
# Start script for BetterBros Props API

set -e

echo "Starting BetterBros Props API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration before starting the server."
    exit 1
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the server
echo "Starting server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000

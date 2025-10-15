#!/bin/bash
# Test script for BetterBros Props API

set -e

echo "Running tests for BetterBros Props API..."

# Activate virtual environment
source venv/bin/activate

# Run linting
echo "Running linting..."
ruff check .

# Run formatting check
echo "Checking code formatting..."
black --check .

# Run tests
echo "Running tests..."
pytest -v

echo "All tests passed!"

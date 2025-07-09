#!/bin/bash

# Watch for file changes and run tests automatically
echo "Setting up automated CI with pytest-watch..."
echo "This will run tests automatically when files change."
echo "Press Ctrl+C to stop watching."
echo "Coverage reports will be generated in htmlcov/ directory."
echo ""

ptw --runner="pytest --cov=src/cpor --cov-report=html --tb=short" -- tests/

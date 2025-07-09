#!/bin/bash
echo "Running tests with coverage..."
pytest --cov=src/cpor --cov-report=html
echo "Coverage report generated in htmlcov/index.html"

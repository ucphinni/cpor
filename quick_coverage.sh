#!/bin/bash

# Quick coverage check - shows coverage percentage and missing lines
echo "=== QUICK COVERAGE CHECK ==="
pytest --cov=src/cpor --cov-report=term-missing tests/ | grep -E "(TOTAL|src/cpor/messages.py)"
echo ""
echo "For detailed HTML coverage report, run: ./run_tests.sh"
echo "For automated testing on file changes, run: ./watch_tests.sh"

#!/bin/bash

# CI Status Check - Show what needs to be done for 100% coverage
echo "=== CI STATUS CHECK ==="
echo "Current coverage status for src/cpor/messages.py:"
echo ""

# Run coverage and extract messages.py info
pytest --cov=src/cpor --cov-report=term-missing tests/ 2>/dev/null | grep "src/cpor/messages.py"

echo ""
echo "=== FAILED TESTS ==="
echo "Tests that need fixing:"
pytest tests/ --tb=no -q 2>/dev/null | grep FAILED

echo ""
echo "=== NEXT STEPS ==="
echo "1. Fix failing tests (type checking issues in from_dict method)"
echo "2. Add tests for uncovered lines shown above"
echo "3. Use './watch_tests.sh' for automated testing during development"
echo "4. Use './run_tests.sh' for full coverage reports"

echo ""
echo "Target: 100% coverage for src/cpor/messages.py"

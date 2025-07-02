#!/bin/bash

echo "🧪 WordPress DB Explorer - Test Runner"
echo

# Check if python3 is available
if command -v python3 &>/dev/null; then
    PYTHON=python3
# Check if python is available
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Could not find python or python3. Please make sure they are installed."
    exit 1
fi

cd "$(dirname "$0")" || exit

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    . venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Please run ./run.sh first to set up the environment."
    exit 1
fi

# Install test dependencies if needed
echo "Ensuring test dependencies are installed..."
pip install pytest pytest-cov > /dev/null 2>&1

echo "Running tests..."
echo

# Run tests with different options based on arguments
if [[ "$1" == "--coverage" ]]; then
    echo "📊 Running tests with coverage report..."
    $PYTHON -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v
elif [[ "$1" == "--unit" ]]; then
    echo "🔬 Running unit tests only..."
    $PYTHON -m pytest tests/ -m unit -v
elif [[ "$1" == "--integration" ]]; then
    echo "🔗 Running integration tests only..."
    $PYTHON -m pytest tests/ -m integration -v
elif [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [option]"
    echo "Options:"
    echo "  --coverage     Run tests with coverage report"
    echo "  --unit         Run unit tests only"
    echo "  --integration  Run integration tests only"
    echo "  --help         Show this help message"
    echo "  (no option)    Run all tests"
else
    echo "🚀 Running all tests..."
    $PYTHON -m pytest tests/ -v
fi

echo
echo "✅ Test run completed!"

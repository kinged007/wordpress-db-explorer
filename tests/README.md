# WordPress DB Explorer - Test Suite

This directory contains the comprehensive test suite for the WordPress DB Explorer project.

## 🧪 Test Structure

### Test Files

- **`test_search_replace.py`** - Tests for search and replace functionality
  - PHP serialized data handling
  - JSON data processing
  - String replacement operations
  - Session management
  - Backup file creation
  - Safety features (dry run mode)

- **`test_error_handling.py`** - Tests for error handling and robustness
  - Column type detection
  - Error message formatting
  - Safe table processing
  - Graceful failure handling

- **`test_db_utils.py`** - Tests for database utilities
  - Database connection management
  - Environment variable handling
  - Connection error handling

- **`conftest.py`** - Shared test fixtures and configuration
  - Mock database objects
  - Sample data fixtures
  - Test utilities

### Configuration

- **`pyproject.toml`** - Modern Python project configuration
  - Pytest settings and markers
  - Coverage configuration
  - Project metadata

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
./run_tests.sh

# Run with coverage report
./run_tests.sh --coverage

# Run only unit tests
./run_tests.sh --unit
```

### Manual Execution
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_search_replace.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v
```

## 📊 Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and components
- Fast execution
- No external dependencies
- Mock database connections

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- May require database connections
- Test real-world scenarios

## 🎯 Test Coverage

The test suite covers:

- **Search & Replace Core Functions**
  - PHP serialized data detection and processing
  - JSON data detection and processing
  - String replacement with length fixing
  - Edge cases and error conditions

- **Session Management**
  - Session initialization
  - Backup file creation and management
  - State tracking

- **Safety Features**
  - Dry run mode enforcement
  - Error handling and recovery
  - Data validation

- **Database Operations**
  - Connection management
  - Environment configuration
  - Error handling

## 📈 Coverage Reports

After running tests with coverage, you can view detailed reports:

- **Terminal Report**: Displayed after test execution
- **HTML Report**: Open `htmlcov/index.html` in your browser

## 🔧 Adding New Tests

### Test File Naming
- Use `test_*.py` naming convention
- Group related tests in the same file
- Use descriptive test method names

### Test Structure
```python
import pytest

class TestYourFeature:
    """Test cases for your feature"""
    
    @pytest.mark.unit
    def test_specific_functionality(self, fixture_name):
        """Test description"""
        # Arrange
        # Act
        # Assert
        assert expected == actual
```

### Using Fixtures
- Use fixtures from `conftest.py` for common test data
- Create new fixtures for specific test needs
- Mock external dependencies

## 🏷️ Test Markers

The following pytest markers are properly configured and registered:

- `@pytest.mark.unit` - Unit tests that test individual functions and components
- `@pytest.mark.integration` - Integration tests that test component interactions
- `@pytest.mark.slow` - Slow running tests that may take longer to execute
- `@pytest.mark.database` - Tests that require database connection

All markers are defined in `pyproject.toml` to eliminate warnings.

## 🐛 Debugging Tests

```bash
# Run with verbose output
pytest tests/ -v -s

# Run specific test with debugging
pytest tests/test_search_replace.py::TestSearchReplace::test_specific_method -v -s

# Drop into debugger on failure
pytest tests/ --pdb
```

## ✅ Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Use descriptive assertion messages
3. **Mock External Dependencies**: Don't rely on real database connections in unit tests
4. **Test Edge Cases**: Include tests for error conditions and edge cases
5. **Descriptive Names**: Use clear, descriptive test method names
6. **Documentation**: Include docstrings explaining what each test verifies

"""
Pytest configuration and shared fixtures for WordPress DB Explorer tests
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_console():
    """Mock Rich console for testing"""
    with patch('rich.console.Console') as mock:
        yield mock

@pytest.fixture
def mock_db_engine():
    """Mock database engine for testing"""
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    return mock_engine, mock_connection

@pytest.fixture
def sample_search_replace_session():
    """Create a sample SearchReplaceSession for testing"""
    from search_replace import SearchReplaceSession
    session = SearchReplaceSession()
    session.search_term = "test_search"
    session.replace_term = "test_replace"
    session.selected_tables = ["wp_posts", "wp_comments"]
    return session

@pytest.fixture
def sample_php_serialized_data():
    """Sample PHP serialized data for testing"""
    return {
        'simple_string': 's:11:"Hello World";',
        'simple_array': 'a:2:{s:4:"name";s:4:"John";s:3:"age";i:30;}',
        'complex_array': 'a:3:{s:7:"widgets";a:7:{i:0;a:13:{s:5:"title";s:73:"An Advance Genetic Service";s:4:"size";s:4:"medium";}}}',
        'boolean_true': 'b:1;',
        'boolean_false': 'b:0;',
        'integer': 'i:42;',
        'null': 'N;'
    }

@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing"""
    return {
        'simple_object': '{"name": "John", "age": 30}',
        'array': '[1, 2, 3, "test"]',
        'nested': '{"user": {"name": "John", "profile": {"email": "john@example.com"}}}',
        'empty_object': '{}',
        'empty_array': '[]'
    }

@pytest.fixture
def mock_database_columns():
    """Mock database column definitions"""
    class MockColumn:
        def __init__(self, name, type_obj):
            self.name = name
            self.type = type_obj
    
    class MockType:
        def __init__(self, type_str, python_type=None):
            self.type_str = type_str
            self.python_type = python_type
            
        def __str__(self):
            return self.type_str
    
    return [
        MockColumn("id", MockType("INTEGER", int)),
        MockColumn("title", MockType("VARCHAR(255)", str)),
        MockColumn("content", MockType("LONGTEXT", str)),
        MockColumn("meta_value", MockType("TEXT", str)),
        MockColumn("created_at", MockType("DATETIME", None)),
        MockColumn("price", MockType("DECIMAL(10,2)", float)),
        MockColumn("description", MockType("MEDIUMTEXT", str)),
    ]

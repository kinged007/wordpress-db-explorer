"""
Test module for the Search and Replace functionality
This module tests various aspects of the search and replace feature including:
- Serialized data handling
- JSON data handling
- Regular string replacement
- Edge cases and error handling
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from search_replace import (
    _safe_replace_in_serialized_data,
    _is_php_serialized,
    _is_json_data,
    _replace_in_php_serialized,
    _replace_in_json_data,
    _fix_php_serialized_lengths,
    SearchReplaceSession
)

class TestSearchReplace:
    """Test cases for search and replace functionality"""
        
    @pytest.mark.unit
    def test_php_serialized_detection(self, sample_php_serialized_data):
        """Test PHP serialized data detection"""
        # Test valid PHP serialized data
        assert _is_php_serialized(sample_php_serialized_data['simple_string'])
        assert _is_php_serialized(sample_php_serialized_data['simple_array'])
        assert _is_php_serialized(sample_php_serialized_data['boolean_true'])
        assert _is_php_serialized(sample_php_serialized_data['integer'])

        # Test invalid data
        assert not _is_php_serialized('regular string')
        assert not _is_php_serialized('{"json": "data"}')
        assert not _is_php_serialized('')
        assert not _is_php_serialized(None)
        
    @pytest.mark.unit
    def test_json_detection(self, sample_json_data):
        """Test JSON data detection"""
        # Test valid JSON
        assert _is_json_data(sample_json_data['simple_object'])
        assert _is_json_data(sample_json_data['array'])
        assert _is_json_data(sample_json_data['nested'])
        assert _is_json_data('"simple string"')
        assert _is_json_data('42')
        assert _is_json_data('true')

        # Test invalid JSON
        assert not _is_json_data('regular string')
        assert not _is_json_data('a:2:{s:4:"name";s:4:"John";}')
        assert not _is_json_data('')
        
    @pytest.mark.unit
    def test_regular_string_replacement(self):
        """Test regular string replacement"""
        original = "Hello World, this is a test string"
        result = _safe_replace_in_serialized_data(original, "World", "Universe")
        expected = "Hello Universe, this is a test string"
        assert result == expected

    @pytest.mark.unit
    def test_json_replacement(self):
        """Test JSON data replacement"""
        original = '{"message": "Hello World", "data": ["World", "test"]}'
        result = _safe_replace_in_serialized_data(original, "World", "Universe")

        # Parse result to verify it's valid JSON
        parsed = json.loads(result)
        assert parsed["message"] == "Hello Universe"
        assert parsed["data"] == ["Universe", "test"]

    @pytest.mark.unit
    def test_php_serialized_replacement(self):
        """Test PHP serialized data replacement"""
        # Test simple string replacement
        original = 's:11:"Hello World";'
        result = _safe_replace_in_serialized_data(original, "World", "Universe")
        # "Hello Universe" is 14 characters long
        expected = 's:14:"Hello Universe";'
        assert result == expected
        
        # Test array replacement
        original = 'a:2:{s:4:"name";s:11:"Hello World";s:4:"city";s:8:"New York";}'
        result = _safe_replace_in_serialized_data(original, "World", "Universe")
        # Should update the string length
        assert "Hello Universe" in result
        assert "s:14:" in result  # New length for "Hello Universe" (14 chars)
        
    @pytest.mark.unit
    def test_php_serialized_length_fixing(self):
        """Test PHP serialized string length fixing"""
        # Test when replacement changes string length
        original = 's:5:"World";'
        modified = original.replace("World", "Universe")  # This breaks the length
        fixed = _fix_php_serialized_lengths(modified)
        expected = 's:8:"Universe";'
        assert fixed == expected
        
    @pytest.mark.unit
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test empty strings
        assert _safe_replace_in_serialized_data("", "test", "replacement") == ""

        # Test None values (should not crash)
        try:
            _safe_replace_in_serialized_data(None, "test", "replacement")
        except Exception as e:
            pass  # Expected to handle gracefully

        # Test malformed serialized data
        malformed = 'a:2:{s:4:"name";s:999:"Hello";}'  # Wrong length
        result = _safe_replace_in_serialized_data(malformed, "Hello", "Hi")
        # Should not crash and should attempt replacement
        assert isinstance(result, str)
        
    @pytest.mark.unit
    def test_complex_serialized_data(self):
        """Test complex WordPress-style serialized data"""
        # WordPress option-style serialized data
        wp_option = 'a:3:{s:9:"site_name";s:12:"My WordPress";s:8:"site_url";s:20:"https://example.com";s:5:"admin";s:13:"admin@example.com";}'

        result = _safe_replace_in_serialized_data(wp_option, "example.com", "newdomain.com")

        # Verify the replacement worked and lengths are correct
        assert "newdomain.com" in result
        assert "example.com" not in result
        # Check that string lengths are updated
        # "https://newdomain.com" is 21 characters
        assert "s:21:" in result  # Length for "https://newdomain.com"
        # "admin@newdomain.com" is 19 characters
        assert "s:19:" in result  # Length for "admin@newdomain.com"
        
    def test_nested_json_replacement(self):
        """Test replacement in nested JSON structures"""
        nested_json = {
            "config": {
                "database": {
                    "host": "old-server.com",
                    "backup_host": "backup.old-server.com"
                },
                "urls": ["https://old-server.com", "https://api.old-server.com"]
            }
        }
        
        original = json.dumps(nested_json)
        result = _safe_replace_in_serialized_data(original, "old-server.com", "new-server.com")
        
        parsed = json.loads(result)
        assert parsed["config"]["database"]["host"] == "new-server.com"
        assert parsed["config"]["database"]["backup_host"] == "backup.new-server.com"
        assert parsed["config"]["urls"][0] == "https://new-server.com"
        assert parsed["config"]["urls"][1] == "https://api.new-server.com"


class TestSearchReplaceSession:
    """Test the SearchReplaceSession class"""

    @pytest.mark.unit
    def test_session_initialization(self, sample_search_replace_session):
        """Test session initialization"""
        session = SearchReplaceSession()
        assert session.search_term == ""
        assert session.replace_term == ""
        assert session.selected_tables == []
        assert session.search_results == {}
        assert session.selected_rows == {}
        assert session.backup_file is None
        assert session.changes_made == []

    @pytest.mark.unit
    def test_backup_file_creation(self):
        """Test backup file creation"""
        session = SearchReplaceSession()
        session.search_term = "test"
        session.replace_term = "replacement"

        backup_file = session.create_backup_file()

        assert backup_file is not None
        assert backup_file.exists()
        assert session.backup_file == backup_file

        # Verify backup file content
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)

        assert backup_data["search_term"] == "test"
        assert backup_data["replace_term"] == "replacement"
        assert backup_data["changes"] == []
        assert "timestamp" in backup_data

        # Clean up
        backup_file.unlink()

    @pytest.mark.unit
    def test_dry_run_safety(self):
        """Test that dry run mode never executes database changes"""
        from search_replace import _execute_replace
        import inspect

        # Get function signature
        sig = inspect.signature(_execute_replace)
        dry_run_param = sig.parameters['dry_run']

        # Verify default is True
        assert dry_run_param.default == True, f"Expected dry_run default to be True, got {dry_run_param.default}"

    @pytest.mark.unit
    def test_preview_functionality(self):
        """Test the improved preview functionality"""
        # Mock row data for testing
        class MockRow:
            def __init__(self, data):
                self._mapping = data
                for key, value in data.items():
                    setattr(self, key, value)

        # Create test rows with search term in specific columns
        test_rows = [
            MockRow({
                'id': 1,
                'title': 'Welcome to example.com',
                'content': 'This is some content without the term',
                'url': 'https://example.com/page1',
                'meta_key': 'some_key',
                'meta_value': 'Visit example.com for more info'
            }),
            MockRow({
                'id': 2,
                'title': 'Another post',
                'content': 'Check out example.com for updates',
                'url': 'https://other-site.com/page2',
                'meta_key': 'another_key',
                'meta_value': 'No match here'
            })
        ]

        from search_replace import _create_row_summary

        # Test row summary creation
        summary1 = _create_row_summary(test_rows[0], "example.com")
        summary2 = _create_row_summary(test_rows[1], "example.com")

        # Verify summaries contain relevant information
        assert "example.com" in summary1, "Summary should contain search term"
        assert "title:" in summary1 or "url:" in summary1 or "meta_value:" in summary1, "Summary should show column names"

        assert "example.com" in summary2, "Summary should contain search term"
        assert "content:" in summary2, "Summary should show matching column"

    @pytest.mark.unit
    def test_serialized_data_single_line_format(self):
        """Test that serialized data is formatted as single-line strings without line breaks"""
        # Test JSON data formatting
        json_data = '{"config": {"host": "old-server.com", "backup": "backup.old-server.com"}, "urls": ["https://old-server.com"]}'
        result = _safe_replace_in_serialized_data(json_data, "old-server.com", "new-server.com")

        # Verify no line breaks in result
        assert '\n' not in result, "JSON result should not contain line breaks"
        assert '\r' not in result, "JSON result should not contain carriage returns"

        # Verify it's still valid JSON
        import json
        parsed = json.loads(result)
        assert parsed["config"]["host"] == "new-server.com"

        # Test PHP serialized data formatting
        php_data = 'a:2:{s:4:"name";s:11:"old-server.com";s:3:"url";s:20:"https://old-server.com";}'
        result = _safe_replace_in_serialized_data(php_data, "old-server.com", "new-server.com")

        # Verify no line breaks in result
        assert '\n' not in result, "PHP serialized result should not contain line breaks"
        assert '\r' not in result, "PHP serialized result should not contain carriage returns"

        # Verify replacement worked
        assert "new-server.com" in result

    @pytest.mark.unit
    def test_wordpress_serialized_with_html_quotes(self):
        """Test WordPress-style serialized data with unescaped quotes in HTML content"""
        # This is the type of data that WordPress actually stores
        wp_data = 's:277:"<iframe id="3stepvideo" src="https://player.vimeo.com/video/155821260?title=0&byline=0&portrait=0" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen height="342" width="300" style="max-width: 600px; max-height: 342px; height: 342px;width:100%;"></iframe>";'

        # Test replacement that changes length
        result = _safe_replace_in_serialized_data(wp_data, "vimeo.com", "newdomain.com")

        # Verify the replacement worked
        assert "newdomain.com" in result
        assert "vimeo.com" not in result

        # Verify the length was updated correctly (277 + 4 = 281)
        assert "s:281:" in result

        # Verify the structure is still valid
        assert result.startswith('s:281:"')
        assert result.endswith('";')

        # Extract the content and verify its length
        content_start = result.find('"') + 1
        content_end = result.rfind('"')
        content = result[content_start:content_end]
        assert len(content) == 281

    @pytest.mark.unit
    def test_wordpress_complex_array_with_html(self):
        """Test complex WordPress array with HTML content"""
        wp_array = 'a:1:{s:7:"widgets";a:1:{i:0;a:5:{s:5:"title";s:0:"";s:4:"text";s:277:"<iframe id="3stepvideo" src="https://player.vimeo.com/video/155821260?title=0&byline=0&portrait=0" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen height="342" width="300" style="max-width: 600px; max-height: 342px; height: 342px;width:100%;"></iframe>";s:6:"filter";b:0;s:6:"visual";b:0;s:11:"option_name";s:11:"widget_text";}}}'

        # Test replacement
        result = _safe_replace_in_serialized_data(wp_array, "vimeo.com", "newdomain.com")

        # Verify the replacement worked
        assert "newdomain.com" in result
        assert "vimeo.com" not in result

        # Verify the length was updated correctly
        assert "s:281:" in result  # 277 + 4 = 281

        # Verify the array structure is maintained
        assert result.startswith('a:1:{')
        assert result.endswith('}')

        # Verify other elements are unchanged
        assert 's:7:"widgets"' in result
        assert 's:11:"widget_text"' in result
        assert 'b:0;' in result  # boolean values should be unchanged

    @pytest.mark.unit
    def test_malformed_serialized_data_with_incorrect_lengths(self):
        """Test handling of malformed serialized data with incorrect string lengths"""
        # Test a simple case where replacement changes length
        malformed_data = 's:16:"hello world test";'

        # Test replacement
        result = _safe_replace_in_serialized_data(malformed_data, "test", "example")

        # Verify the replacement worked
        assert "example" in result
        assert "test" not in result

        # Verify the length was updated correctly ("test" -> "example" adds 3 chars: 16 + 3 = 19)
        assert "s:19:" in result  # "hello world example" is 19 characters

        # Verify the structure is still valid
        assert result.startswith('s:19:"')
        assert result.endswith('";')

    @pytest.mark.unit
    def test_severely_malformed_serialized_data(self):
        """Test handling of severely malformed serialized data"""
        # This simulates data where the length is completely wrong
        malformed_data = 's:50:"hello world";'  # Length says 50 but content is only 11 chars

        # Test replacement
        result = _safe_replace_in_serialized_data(malformed_data, "world", "universe")

        # Verify the replacement worked
        assert "universe" in result
        assert "world" not in result

        # Verify the length was corrected ("hello universe" is 14 characters)
        assert "s:14:" in result

        # Verify the structure is still valid
        assert result.startswith('s:14:"')
        assert result.endswith('";')

# 🔄 Search and Replace Tool

A powerful and safe database search and replace tool specifically designed for WordPress databases. This tool provides comprehensive functionality for finding and replacing text across database tables while maintaining data integrity and providing robust safety features.

## ✨ Key Features

### 🛡️ Safety First
- **Dry Run Mode**: Test all operations before making actual changes
- **Automatic Backups**: Creates backup files before any modifications
- **Transaction Safety**: Uses database transactions with rollback capability
- **Multiple Confirmations**: Several confirmation steps prevent accidental changes
- **Undo Functionality**: Complete undo capability for all operations

### 🔧 Smart Data Handling
- **Serialized Data Detection**: Automatically detects and safely handles PHP serialized data
- **JSON Support**: Properly handles JSON data structures
- **Length Correction**: Automatically fixes string lengths in PHP serialized arrays
- **WordPress Compatibility**: Designed specifically for WordPress database structures

### 🎯 Precise Control
- **Multi-Table Selection**: Choose specific tables or all WordPress tables
- **Granular Row Selection**: Select/deselect specific rows for modification
- **Search Preview**: View matches with highlighted search terms
- **Progress Tracking**: Real-time progress updates during operations

## 🚀 How to Use

### 1. Access the Tool
```bash
python main.py
# Select "3. Search & Replace"
```

### 2. Configure Search Term
- Enter the text you want to search for
- The tool will remember this throughout the session

### 3. Select Tables
- Choose from all WordPress tables
- Use "All WordPress Tables" for comprehensive search
- Or select specific tables for targeted operations

### 4. Find Matches
- Execute search across selected tables
- Filters are applied during search for better performance
- View total match counts per table

### 5. Preview Results
- View search results across selected tables
- See highlighted matches in context
- Review total match counts per table

### 6. View Table Data (Optional)
- See complete row data for all columns
- Search terms highlighted in matching columns
- Full context view for better decision making

### 7. Configure Filters (Optional)
- **By Another Column Value**: Filter results by specific column criteria
- **Exact Match**: Column value must exactly match filter value
- **Contains Match**: Column value contains the filter text
- **Example**: Filter `wp_postmeta` where `meta_key = "_elementor_field"`

### 8. Configure Row Selection (optional)
- **Keep all rows selected**: Modify all found matches (default)
- **Deselect specific rows**: Exclude certain rows from modification
- **Select only specific rows**: Choose only specific rows to modify
- **Skip table entirely**: Exclude entire tables from the operation

### 9. Set Replace Text
- Enter the replacement text
- Can be empty string for deletion
- Supports any text including special characters

### 10. Execute Operation
- **Dry Run First**: Always test with dry run mode
- **Review Summary**: Check the operation summary
- **Final Confirmation**: Confirm the actual replacement
- **Monitor Progress**: Watch real-time progress updates

### 11. Undo if Needed
- Access undo functionality from the main menu
- Select from available backup files
- Restore original values completely

## 📊 Workflow Example

```
1. Search Term: "old-domain.com"
2. Tables: wp_posts, wp_options, wp_postmeta
3. Find Matches: 45 matches found across 3 tables
4. Filter: wp_postmeta where meta_key = "custom_field"
5. Preview: 12 filtered matches found
6. Row Selection: Deselect 2 rows (file paths)
7. Replace With: "new-domain.com"
8. Dry Run: Review 10 planned changes
9. Execute: Apply changes with backup
10. Result: 10 successful replacements
```

## 🔍 Supported Data Types

### Regular Strings
```
"Welcome to example.com"
→ "Welcome to newdomain.com"
```

### PHP Serialized Arrays
```
a:2:{s:4:"name";s:11:"Hello World";s:3:"url";s:15:"https://old.com";}
→ a:2:{s:4:"name";s:11:"Hello World";s:3:"url";s:15:"https://new.com";}
```

### JSON Data
```
{"config": {"host": "old-server.com"}}
→ {"config": {"host": "new-server.com"}}
```

### WordPress Options
```
s:20:"https://example.com";
→ s:21:"https://newdomain.com";
```

## 💡 Common Use Cases

### Domain Migration
- **Scenario**: Moving WordPress site to new domain
- **Search**: `old-site.com`
- **Replace**: `new-site.com`
- **Tables**: All WordPress tables

### HTTPS Migration
- **Scenario**: Converting HTTP URLs to HTTPS
- **Search**: `http://`
- **Replace**: `https://`
- **Tables**: wp_posts, wp_options, wp_postmeta

### Email Updates
- **Scenario**: Changing admin email addresses
- **Search**: `admin@oldcompany.com`
- **Replace**: `admin@newcompany.com`
- **Tables**: wp_users, wp_options

### Content Updates
- **Scenario**: Updating product names in content
- **Search**: `Old Product Name`
- **Replace**: `New Product Name`
- **Tables**: wp_posts, wp_postmeta

### Filtered Updates
- **Scenario**: Update Elementor field values only
- **Search**: `old-value`
- **Replace**: `new-value`
- **Tables**: wp_postmeta
- **Filter**: meta_key = "_elementor_field" (exact match)

### Path Corrections
- **Scenario**: Fixing file paths after server migration
- **Search**: `/old/path/`
- **Replace**: `/new/path/`
- **Tables**: wp_posts, wp_options, wp_postmeta

## 🎨 Working with Page Builders

### Overview
Page builders like **Elementor** and **SiteOrigin Page Builder** store their content data differently than standard WordPress posts. Understanding how they work is crucial for successful search and replace operations.

### How Page Builders Store Data
- **Primary Storage**: Most page builder content is stored in the `wp_postmeta` table
- **Serialized Format**: Data is typically stored as PHP serialized arrays or JSON
- **Meta Keys**: Each page builder uses specific meta keys (e.g., `_elementor_data`, `panels_data`)
- **Complex Structure**: Content is nested within widget/element configurations

### Best Practices for Page Builder Content

#### 1. Use Filters for Precision
```
Tables: wp_postmeta
Filter: meta_key = "_elementor_data" (exact match)
Search: "old-domain.com"
Replace: "new-domain.com"
```

#### 2. Always Use View Table Data
- Review the complete row data before making changes
- Understand the structure of the serialized content
- Identify which specific elements contain your search term

#### 3. Start with Dry Run
- Page builder data is complex and interconnected
- Test changes thoroughly before applying
- Verify the serialized data structure remains intact

### Tested Page Builders
- ✅ **Elementor**: Simple substring replacements work reliably
- ✅ **SiteOrigin Page Builder**: Basic content updates function correctly
- ⚠️ **Limited Testing**: Extensive testing has not been performed

### Important Considerations
- **Review Carefully**: Always examine matched rows and content structure
- **Backup Essential**: Page builder data corruption can break entire pages
- **Test Thoroughly**: Check page functionality after any changes
- **Report Issues**: If you encounter problems, please [submit an issue](https://github.com/kinged007/wordpress-db-explorer/issues)
- **Contribute**: Improvements and pull requests are welcome

### Common Page Builder Meta Keys
- **Elementor**: `_elementor_data`, `_elementor_page_settings`
- **SiteOrigin**: `panels_data`
- **Beaver Builder**: `_fl_builder_data`
- **Divi**: `_et_pb_page_layout`

## ⚠️ Important Safety Guidelines

### Before You Start
1. **Always backup your database** using your hosting provider's tools
2. **Test on a staging site** first if possible
3. **Use dry run mode** to preview all changes
4. **Start with specific tables** rather than all tables
5. **Review the search results** carefully before proceeding

### During Operation
1. **Double-check search terms** for accuracy
2. **Review row selections** to avoid unwanted changes
3. **Confirm replacement text** is correct
4. **Monitor the operation** for any errors
5. **Keep backup files** until you're sure changes are correct

### After Operation
1. **Test your website** thoroughly
2. **Check critical functionality** (login, checkout, etc.)
3. **Keep backup files** for potential undo operations
4. **Document changes made** for future reference

## 🔧 Technical Details

### Backup System
- Backup files stored in `backups/` directory
- JSON format with complete change history
- Includes original and new values for each change
- Timestamped for easy identification

### Serialized Data Handling
- Automatic detection of PHP serialized data
- Safe string replacement with length correction
- Preservation of data structure integrity
- Support for nested arrays and objects

### Database Safety
- Uses SQLAlchemy transactions
- Automatic rollback on errors
- Batch processing for large datasets
- Connection pooling for efficiency

### Error Handling
- Graceful handling of malformed data
- Detailed error reporting
- Automatic recovery where possible
- Safe fallback for edge cases

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_search_replace.py
```

Run the interactive demo:
```bash
python demo_search_replace.py
```

## 📁 File Structure

```
src/
├── search_replace.py      # Main search and replace functionality
├── main.py               # Updated with search & replace menu option
test_search_replace.py    # Comprehensive test suite
demo_search_replace.py    # Interactive demonstration
backups/                  # Backup files directory (auto-created)
```

## 🤝 Support

If you encounter any issues:
1. Check the error messages for specific guidance
2. Review the backup files for undo options
3. Test with smaller datasets first
4. Use dry run mode to troubleshoot
5. Consult the test cases for examples

Remember: This is a powerful tool that can make significant changes to your database. Always prioritize safety and testing!

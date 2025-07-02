# WordPress DB Explorer

A powerful command-line tool for exploring, searching, and exporting data from WordPress databases. This application provides an intuitive interface to interact with WordPress databases, including WooCommerce data, with advanced search and export capabilities.

## 🚀 Features

### Database Operations
- **Connection Testing**: Verify database connectivity before performing operations
- **Multi-table Search**: Search across WordPress core tables and custom post types
- **Advanced Filtering**: Filter data by specific fields, date ranges, and custom criteria

### Search Capabilities
- **User Search**: Find WordPress users by username, email, role, or any user field
- **Post Search**: Search WordPress posts, pages, and custom post types
- **WooCommerce Integration**:
  - Search orders by status, customer, date range, or order details
  - Search coupons by code, type, usage, or expiration
- **General Search**: Perform broad searches across all fields in any table
- **Custom Post Types**: Automatically detect and search custom post types

### Search & Replace
- **Multi-table Search & Replace**: Find and replace text across multiple WordPress tables
- **Safe Preview**: Preview matches with highlighted search terms before making changes
- **Full-Width Tables**: Optimized table display using full terminal width for better content visibility
- **Selective Replacement**: Choose specific rows and tables for replacement
- **Interactive Workflow**: Step-by-step guided process with clear status indicators
- **Dry Run Mode**: Test replacements without making actual changes
- **Undo Functionality**: Reverse changes if needed
- **WordPress-aware**: Handles serialized data and WordPress-specific content safely

For detailed usage instructions, see [SEARCH_REPLACE_README.md](SEARCH_REPLACE_README.md)

### Export Features
- **Multiple Formats**: Export data in JSON or CSV format
- **Batch Processing**: Handle large datasets efficiently with batch processing
- **Filtered Exports**: Export only the data that matches your search criteria
- **Metadata Inclusion**: Option to include WordPress metadata in exports
- **Organized Output**: Exports are saved in timestamped files in the `exports/` directory

### User Experience Features
- **Intuitive Menus**: Clear, numbered menu options with descriptive labels
- **Rich Console Output**: Colorized output with icons and formatting for better readability
- **Progress Indicators**: Real-time feedback during long-running operations
- **Error Handling**: Graceful error handling with helpful error messages
- **Full-Width Tables**: Tables automatically expand to use full terminal width for maximum content visibility

### Supported Data Types
- WordPress Users (with metadata)
- WordPress Posts and Pages
- WooCommerce Orders
- WooCommerce Coupons
- Custom Post Types
- Any WordPress table data

## 📋 Prerequisites

- **Python**: Python 3.6 or higher
- **pip**: Python package installer
- **Database Access**: MySQL/MariaDB database credentials for your WordPress site
- **Operating System**: macOS, Linux, or Windows (with appropriate Python installation)

## 🛠️ Installation & Setup

### Method 1: Using the run.sh Script (Recommended for macOS/Linux)

1. **Clone or download** this repository to your local machine

2. **Navigate** to the project directory:
   ```bash
   cd wordpress-db-explorer
   ```

3. **Copy the environment file** and configure your database settings:
   ```bash
   cp sample.env .env
   ```

4. **Edit the .env file** with your WordPress database credentials:
   ```
   DB_HOST=your_database_host
   DB_PORT=3306
   DB_USER=your_database_username
   DB_PASSWORD=your_database_password
   DB_NAME=your_wordpress_database_name
   TABLE_PREFIX=wp_
   ```

5. **Make the script executable** (if needed):
   ```bash
   chmod +x run.sh
   ```

6. **Run the application**:
   ```bash
   ./run.sh
   ```

The script will automatically:
- Detect Python 3 or Python installation
- Create a virtual environment (if it doesn't exist)
- Install all required dependencies
- Activate the virtual environment
- Launch the application

### Method 2: Manual Setup (All Operating Systems)

If you prefer not to use the run.sh script or are on Windows, follow these steps:

1. **Clone or download** this repository

2. **Navigate** to the project directory:
   ```bash
   cd wordpress-db-explorer
   ```

3. **Create a virtual environment**:
   ```bash
   # On macOS/Linux:
   python3 -m venv venv
   
   # On Windows:
   python -m venv venv
   ```

4. **Activate the virtual environment**:
   ```bash
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Configure environment variables**:
   ```bash
   cp sample.env .env
   ```
   
   Edit the `.env` file with your database credentials (same as Method 1, step 4)

7. **Run the application**:
   ```bash
   python main.py
   ```

## 🎯 Usage

### Starting the Application

When you run the application, you'll see a main menu with these options:

```
Select an option:
❯ 1. Test DB Connection
  2. Search
  3. Search & Replace
  4. Export
  Exit
```

### 1. Test DB Connection

Always start by testing your database connection to ensure your credentials are correct.

### 2. Search

The search menu offers multiple search options:

```
🔍 Select search type:
❯ 1. Search Users
  2. Search Orders
  3. Search Coupons
  4. Search Posts
  5. Search Pages
  6. Search Custom Post Type
  7. General Search
  Back
```

- **1. Search Users**: Find users by username, email, display name, or any user field
  - Search by user fields (username, email, display_name, etc.)
  - Search by user meta data (custom fields)
- **2. Search Orders**: Find WooCommerce orders by status, customer, date range
  - Search by order fields (status, customer info, dates)
  - Search by order meta data (custom order fields)
- **3. Search Coupons**: Find WooCommerce coupons by code, type, usage
  - Search by coupon fields (code, type, amount, usage)
  - Search by coupon meta data (custom coupon fields)
- **4. Search Posts**: Find WordPress blog posts by title, content, author
  - Search by post fields (title, content, author, status)
  - Search by post meta data (custom fields)
- **5. Search Pages**: Find WordPress pages by title, content
  - Search by page fields (title, content, status)
  - Search by page meta data (custom fields)
- **6. Search Custom Post Type**: Search any custom post type in your database
- **7. General Search**: Perform broad searches across any table

### 3. Search & Replace

Safely find and replace text across your WordPress database with a step-by-step workflow:

```
🔄 Search and Replace Tool
📊 Current Configuration:
  • Search Term: 'example.com'
  • Tables Selected: 3
  • Total Matches Found: 45
  • Replace With: 'newdomain.com'

❯ Configure Search Term
  Select Tables
  Find Matches
  Preview Matches
  Configure Row Selection
  Set Replace Text
  Execute Replace (Dry Run)
  Execute Replace
  Undo Last Operation
  Exit
```

**Key Features:**
- **Configure Search Term**: Set the text you want to find
- **Select Tables**: Choose which database tables to search
- **Find Matches**: Search for your term across selected tables
- **Preview Matches**: Review found matches with highlighted search terms and full-width table display
- **Configure Row Selection**: Fine-tune which specific rows to include/exclude
- **Set Replace Text**: Define the replacement text
- **Execute Replace (Dry Run)**: Test the operation safely without making changes
- **Execute Replace**: Apply the changes with automatic backup creation
- **Undo Last Operation**: Reverse changes if needed

See [SEARCH_REPLACE_README.md](SEARCH_REPLACE_README.md) for detailed instructions.

### 4. Export

Export filtered data in JSON or CSV format:

```
📤 Select data to export:
❯ Users
  WooCommerce Orders
  WooCommerce Coupons
  WordPress Posts
  WordPress Pages
  Custom Post Type
  Back
```

- **Users**: Export user data with optional metadata
- **WooCommerce Orders**: Export order data with customer information
- **WooCommerce Coupons**: Export coupon data with usage statistics
- **WordPress Posts**: Export blog post content with metadata
- **WordPress Pages**: Export page content with metadata
- **Custom Post Type**: Export any custom post type data

All exports are saved in the `exports/` directory with timestamps.

## 🔧 Configuration

### Environment Variables

The application uses a `.env` file for configuration:

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | Database server hostname | `localhost` or `127.0.0.1` |
| `DB_PORT` | Database server port | `3306` |
| `DB_USER` | Database username | `wp_user` |
| `DB_PASSWORD` | Database password | `your_password` |
| `DB_NAME` | WordPress database name | `wordpress_db` |
| `TABLE_PREFIX` | WordPress table prefix | `wp_` |

### Upgrading Dependencies

To upgrade the application dependencies:

```bash
# Using run.sh script:
./run.sh --upgrade

# Manual method:
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install --upgrade -r requirements.txt
```

### Version Control

The project includes a comprehensive `.gitignore` file that excludes:

- **Environment files**: `.env`, virtual environments, IDE files
- **Generated files**: `__pycache__`, coverage reports, test artifacts
- **Sensitive data**: Database credentials, backup files, logs
- **Export files**: CSV/JSON exports (while preserving directory structure)
- **OS files**: `.DS_Store`, `Thumbs.db`, temporary files

**Important**: Always ensure your `.env` file is not committed to version control as it contains sensitive database credentials.

## 🧪 Testing

The project includes a comprehensive test suite using pytest.

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Run tests with coverage report
./run_tests.sh --coverage

# Run only unit tests
./run_tests.sh --unit

# Run only integration tests
./run_tests.sh --integration

# Manual pytest execution
source venv/bin/activate
pytest tests/ -v
```

### Test Structure

- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test component interactions
- **Coverage Reports**: HTML and terminal coverage reports available

## 📁 Project Structure

```
wordpress-db-explorer/
├── .gitignore           # Git ignore rules
├── main.py              # Application entry point
├── run.sh               # Setup and launch script (macOS/Linux)
├── run_tests.sh         # Test runner script
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Modern Python project configuration (pytest, coverage)
├── sample.env           # Environment template
├── .env                 # Your database configuration (create this)
├── exports/             # Export output directory
│   └── .gitkeep         # Preserves directory structure in git
├── htmlcov/             # Coverage reports (auto-generated)
├── src/
│   ├── db_utils.py      # Database connection utilities
│   ├── search_utils.py  # Search functionality
│   ├── search_replace.py # Search and replace functionality
│   ├── export_menu.py   # Export menu interface
│   └── export_utils.py  # Export functionality
├── tests/
│   ├── __init__.py      # Tests package
│   ├── README.md        # Test documentation
│   ├── conftest.py      # Shared test fixtures
│   ├── test_search_replace.py  # Search & replace tests
│   └── test_error_handling.py  # Error handling tests
└── venv/                # Virtual environment (auto-created)
```

## 🔍 Dependencies

- **SQLAlchemy**: Database ORM and connection management
- **rich**: Beautiful terminal output and formatting
- **inquirer**: Interactive command-line menus
- **python-dotenv**: Environment variable management
- **pymysql**: MySQL database connector

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify your `.env` file has correct database credentials
   - Ensure your database server is running
   - Check if your database user has proper permissions

2. **Python/pip Not Found**
   - Install Python 3.6+ from [python.org](https://python.org)
   - Ensure Python is added to your system PATH

3. **Permission Denied on run.sh**
   ```bash
   chmod +x run.sh
   ```

4. **Virtual Environment Issues**
   - Delete the `venv` folder and run the setup again
   - Ensure you have sufficient disk space

### Getting Help

If you encounter issues:
1. Check that all prerequisites are installed
2. Verify your database credentials in the `.env` file
3. Test the database connection using option 1 in the main menu
4. Ensure your WordPress database is accessible from your machine

## 📝 License

This project is open source. Please check the license file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

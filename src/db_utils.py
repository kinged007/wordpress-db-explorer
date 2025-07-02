import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import text  # Import text for raw SQL queries
from rich.console import Console
from dotenv import load_dotenv  # Import dotenv

console = Console()

# Load environment variables from the .env file with override enabled
load_dotenv(override=True)

# Global variables for lazy database connection
_engine = None
_inspector = None
_connection_status = None
_connection_error = None

def validate_db_config():
    """Validate that all required database configuration is present."""
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == '':
            missing_vars.append(var)

    if missing_vars:
        return False, f"Missing required environment variables: {', '.join(missing_vars)}"

    return True, None

def get_db_engine():
    """Get database engine with lazy initialization and error handling."""
    global _engine, _connection_status, _connection_error

    if _engine is not None:
        return _engine

    # Validate configuration first
    config_valid, config_error = validate_db_config()
    if not config_valid:
        _connection_status = "config_error"
        _connection_error = config_error
        raise Exception(config_error)

    try:
        db_host = os.getenv('DB_HOST')
        db_port = int(os.getenv('DB_PORT', 3306))
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')

        db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        _engine = create_engine(db_url)
        return _engine
    except Exception as e:
        _connection_status = "engine_error"
        _connection_error = str(e)
        raise

def get_db_inspector():
    """Get database inspector with lazy initialization."""
    global _inspector

    if _inspector is not None:
        return _inspector

    try:
        engine = get_db_engine()
        _inspector = inspect(engine)
        return _inspector
    except Exception as e:
        raise Exception(f"Failed to create database inspector: {e}")

def test_db_connection():
    """Test database connection and return status."""
    global _connection_status, _connection_error

    try:
        engine = get_db_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        _connection_status = "connected"
        _connection_error = None
        console.print("✅ Database connection successful!", style="bold green")
        return True, None
    except Exception as e:
        _connection_status = "failed"
        _connection_error = str(e)
        console.print(f"❌ Database connection failed: {e}", style="bold red")
        return False, str(e)

def get_connection_status():
    """Get current database connection status without attempting connection."""
    return _connection_status, _connection_error

def check_db_connection_with_friendly_error():
    """Check database connection and display user-friendly error messages."""
    try:
        # First validate configuration
        config_valid, config_error = validate_db_config()
        if not config_valid:
            console.print("❌ Database Configuration Error", style="bold red")
            console.print(f"   {config_error}", style="red")
            console.print("   Please check your .env file and ensure all database credentials are set.", style="yellow")
            return False

        # Test actual connection
        success, error = test_db_connection()
        if not success:
            console.print("❌ Database Connection Error", style="bold red")

            # Provide more specific error messages
            if "nodename nor servname provided" in error or "Name or service not known" in error:
                console.print("   Cannot resolve database hostname. Please check:", style="red")
                console.print(f"   - DB_HOST is correct: {os.getenv('DB_HOST')}", style="yellow")
                console.print("   - Network connectivity to the database server", style="yellow")
                console.print("   - Hosting provider allows remote connections from your IP", style="yellow")
            elif "Access denied" in error:
                console.print("   Database authentication failed. Please check:", style="red")
                console.print(f"   - DB_USER: {os.getenv('DB_USER')}", style="yellow")
                console.print("   - DB_PASSWORD is correct", style="yellow")
            elif "Unknown database" in error:
                console.print("   Database does not exist. Please check:", style="red")
                console.print(f"   - DB_NAME: {os.getenv('DB_NAME')}", style="yellow")
            elif "Connection refused" in error:
                console.print("   Cannot connect to database server. Please check:", style="red")
                console.print(f"   - DB_HOST: {os.getenv('DB_HOST')}", style="yellow")
                console.print(f"   - DB_PORT: {os.getenv('DB_PORT', '3306')}", style="yellow")
                console.print("   - Database server is running", style="yellow")
            else:
                console.print(f"   {error}", style="red")

            console.print("\n   💡 Tip: Use 'Test DB Connection' from the main menu to retry", style="cyan")
            return False

        return True

    except Exception as e:
        console.print(f"❌ Unexpected error checking database connection: {e}", style="bold red")
        return False

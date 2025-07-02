import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import text  # Import text for raw SQL queries
from rich.console import Console
from dotenv import load_dotenv  # Import dotenv

console = Console()

# Load environment variables from the .env file with override enabled
load_dotenv(override=True)

def get_db_engine():
    db_host = os.getenv('DB_HOST')
    db_port = int(os.getenv('DB_PORT', 3306))  # Ensure DB_PORT is converted to an integer
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')

    db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    # print(db_url)  # Debugging line to check the DB URL
    return create_engine(db_url)

def test_db_connection():
    try:
        engine = get_db_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))  # Use text() for raw SQL
        console.print("✅ Database connection successful!", style="bold green")
    except Exception as e:
        console.print(f"❌ Database connection failed: {e}", style="bold red")

# Import search functionality from search_utils to maintain backward compatibility
from src.search_utils import search_database

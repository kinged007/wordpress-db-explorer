import inquirer
from rich.console import Console
from src.db_utils import test_db_connection, check_db_connection_with_friendly_error
from src.search_utils import search_database
from src.export_menu import export_menu
from src.search_replace import search_and_replace_menu

console = Console()

def main():
    # Display welcome message and database connection status
    console.print("🔍 WordPress Database Explorer", style="bold blue")
    console.print("=" * 50, style="blue")

    # Check database connection status on startup
    console.print("\n📡 Checking database connection...", style="cyan")
    db_connected = check_db_connection_with_friendly_error()

    if not db_connected:
        console.print("\n⚠️  Some features may not work until database connection is established.", style="yellow")

    console.print("\n" + "=" * 50, style="blue")

    while True:
        questions = [
            inquirer.List(
                "option",
                message="Select an option",
                choices=["1. Test DB Connection", "2. Search", "3. Search & Replace", "4. Export", "Exit"],
            )
        ]
        answers = inquirer.prompt(questions)

        # Handle case where user cancels (Ctrl+C)
        if answers is None:
            console.print("\n👋 Exiting application. Goodbye!", style="bold green")
            break

        if answers["option"] == "1. Test DB Connection":
            test_db_connection()
        elif answers["option"] == "2. Search":
            search_database()
        elif answers["option"] == "3. Search & Replace":
            search_and_replace_menu()
        elif answers["option"] == "4. Export":
            export_menu()
        elif answers["option"] == "Exit":
            console.print("👋 Exiting application. Goodbye!", style="bold green")
            break

if __name__ == "__main__":
    main()

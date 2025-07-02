import inquirer
from rich.console import Console
from src.db_utils import test_db_connection
from src.search_utils import search_database
from src.export_menu import export_menu
from src.search_replace import search_and_replace_menu

console = Console()

def main():
    while True:
        questions = [
            inquirer.List(
                "option",
                message="Select an option",
                choices=["1. Test DB Connection", "2. Search", "3. Search & Replace", "4. Export", "Exit"],
            )
        ]
        answers = inquirer.prompt(questions)

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

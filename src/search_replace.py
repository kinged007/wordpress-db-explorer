import os
import json
import re
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import inquirer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from sqlalchemy import inspect
from sqlalchemy.sql import text
from dotenv import load_dotenv

from src.db_utils import get_db_engine

console = Console()
load_dotenv(override=True)

# Global database connection objects
engine = get_db_engine()
inspector = inspect(engine)
table_prefix = os.getenv('TABLE_PREFIX', '')

# Create backups directory
BACKUPS_DIR = Path("backups")
BACKUPS_DIR.mkdir(exist_ok=True)

class SearchReplaceSession:
    """Manages a search and replace session with undo capabilities"""
    
    def __init__(self):
        self.search_term = ""
        self.replace_term = ""
        self.selected_tables = []
        self.search_results = {}  # table_name: [rows with matches]
        self.selected_rows = {}   # table_name: [row_ids to modify]
        self.backup_file = None
        self.changes_made = []
        
    def create_backup_file(self):
        """Create a backup file for this session"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_file = BACKUPS_DIR / f"search_replace_backup_{timestamp}.json"
        
        backup_data = {
            "timestamp": timestamp,
            "search_term": self.search_term,
            "replace_term": self.replace_term,
            "changes": []
        }
        
        with open(self.backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
            
        return self.backup_file

def search_and_replace_menu():
    """Main search and replace menu function"""
    console.print("\n🔄 Search and Replace Tool", style="bold blue")
    console.print("This tool allows you to search for text across database tables and replace it safely.", style="dim")
    console.print("⚠️  This is a powerful tool - use with caution!", style="bold yellow")
    
    session = SearchReplaceSession()
    
    while True:
        # Step 1: Get search term
        if not session.search_term:
            if not _get_search_term(session):
                return  # User cancelled
        
        # Main operation loop
        choice = _show_main_menu(session)
        
        if choice == "Configure Search Term":
            if not _get_search_term(session):
                return
        elif choice == "Select Tables":
            _select_tables(session)
        elif choice == "Find Matches":
            _find_matches(session)
        elif choice == "Preview Matches":
            _preview_matches(session)
        elif choice == "Configure Row Selection":
            _configure_row_selection(session)
        elif choice == "Set Replace Text":
            _get_replace_term(session)
        elif choice == "Execute Replace (Dry Run)":
            _execute_replace(session, dry_run=True)
        elif choice == "Execute Replace":
            _execute_replace(session, dry_run=False)
        elif choice == "Undo Last Operation":
            _undo_last_operation()
        elif choice == "Exit":
            break

def _get_search_term(session: SearchReplaceSession) -> bool:
    """Get the search term from user"""
    questions = [
        inquirer.Text(
            "search_term",
            message="Enter the text to search for",
            default=session.search_term
        )
    ]
    
    answers = inquirer.prompt(questions)
    if not answers or not answers["search_term"].strip():
        return False
        
    session.search_term = answers["search_term"].strip()
    # Reset dependent data when search term changes
    session.search_results = {}
    session.selected_rows = {}
    return True

def _show_main_menu(session: SearchReplaceSession) -> str:
    """Show the main menu and return user choice"""
    status_info = []
    status_info.append(f"Search Term: '{session.search_term}'")
    
    if session.selected_tables:
        status_info.append(f"Tables Selected: {len(session.selected_tables)}")
    else:
        status_info.append("Tables Selected: None")
        
    if session.search_results:
        total_matches = sum(len(results) for results in session.search_results.values())
        status_info.append(f"Total Matches Found: {total_matches}")
    
    if session.replace_term:
        status_info.append(f"Replace With: '{session.replace_term}'")
    
    console.print("\n📊 Current Configuration:", style="bold")
    for info in status_info:
        console.print(f"  • {info}", style="dim")
    
    choices = [
        "Configure Search Term",
        "Select Tables",
        "Find Matches",
        "Preview Matches",
        "Configure Row Selection",
        "Set Replace Text",
        "Execute Replace (Dry Run)",
        "Execute Replace",
        "Undo Last Operation",
        "Exit"
    ]
    
    # Disable certain options based on current state
    if not session.selected_tables:
        choices = [c for c in choices if c not in ["Find Matches", "Preview Matches", "Configure Row Selection", "Execute Replace (Dry Run)", "Execute Replace"]]

    if not session.search_results:
        choices = [c for c in choices if c not in ["Preview Matches", "Configure Row Selection", "Execute Replace (Dry Run)", "Execute Replace"]]
        
    if not session.replace_term:
        choices = [c for c in choices if c not in ["Execute Replace (Dry Run)", "Execute Replace"]]
    
    questions = [
        inquirer.List(
            "choice",
            message="Select an action",
            choices=choices
        )
    ]
    
    answers = inquirer.prompt(questions)
    return answers["choice"] if answers else "Exit"

def _select_tables(session: SearchReplaceSession):
    """Allow user to select tables for search and replace"""
    try:
        # Get all tables from database
        all_tables = inspector.get_table_names()
        
        if not all_tables:
            console.print("❌ No tables found in database!", style="bold red")
            return
            
        # Filter WordPress tables (those with the table prefix)
        wp_tables = [table for table in all_tables if table.startswith(table_prefix)]
        
        if not wp_tables:
            console.print(f"❌ No WordPress tables found with prefix '{table_prefix}'!", style="bold red")
            return
        
        # Add special options
        choices = ["All WordPress Tables", "None"] + wp_tables
        
        questions = [
            inquirer.Checkbox(
                "tables",
                message="Select tables to search (use SPACE to select, ENTER to confirm)",
                choices=choices,
                default=session.selected_tables
            )
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return
            
        selected = answers["tables"]
        
        if "All WordPress Tables" in selected:
            session.selected_tables = wp_tables
        elif "None" in selected:
            session.selected_tables = []
        else:
            session.selected_tables = [table for table in selected if table not in ["All WordPress Tables", "None"]]
        
        # Reset search results when tables change
        session.search_results = {}
        session.selected_rows = {}
        
        console.print(f"✅ Selected {len(session.selected_tables)} tables", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Error selecting tables: {e}", style="bold red")

def _find_matches(session: SearchReplaceSession):
    """Find matches across selected tables"""
    if not session.selected_tables:
        console.print("❌ No tables selected!", style="bold red")
        return
        
    if not session.search_term:
        console.print("❌ No search term specified!", style="bold red")
        return
    
    console.print(f"\n🔍 Searching for '{session.search_term}' in {len(session.selected_tables)} tables...", style="bold blue")
    
    session.search_results = {}
    total_matches = 0
    
    try:
        with engine.connect() as connection:
            for table_name in session.selected_tables:
                try:
                    console.print(f"Searching {table_name}...", style="dim")

                    # Get table columns with better error handling
                    try:
                        columns = inspector.get_columns(table_name)
                    except Exception as col_error:
                        console.print(f"  ⚠️  Could not get columns for {table_name}: {col_error}", style="yellow")
                        continue

                    if not columns:
                        console.print(f"  ⚠️  No columns found in {table_name}", style="yellow")
                        continue

                    # Find text columns with safer type checking
                    text_columns = []
                    for col in columns:
                        try:
                            # Check if column type is likely to contain text
                            col_type_str = str(col['type']).upper()
                            if any(text_type in col_type_str for text_type in ['TEXT', 'VARCHAR', 'CHAR', 'LONGTEXT', 'MEDIUMTEXT', 'TINYTEXT']):
                                text_columns.append(col['name'])
                            elif hasattr(col['type'], 'python_type'):
                                if col['type'].python_type in (str, type(None)):
                                    text_columns.append(col['name'])
                        except Exception as type_error:
                            # If we can't determine the type, include it anyway for text search
                            console.print(f"  ⚠️  Could not determine type for column {col['name']} in {table_name}, including anyway", style="dim")
                            text_columns.append(col['name'])

                    if not text_columns:
                        console.print(f"  ⚪ No text columns found in {table_name}", style="dim")
                        continue

                    # Build search query for text columns
                    where_conditions = []
                    for col in text_columns:
                        where_conditions.append(f"`{col}` LIKE :search_term")

                    where_clause = " OR ".join(where_conditions)

                    # Execute search query
                    query = text(f"SELECT * FROM `{table_name}` WHERE {where_clause}")
                    result = connection.execute(query, {"search_term": f"%{session.search_term}%"})

                    rows = result.fetchall()
                    if rows:
                        session.search_results[table_name] = rows
                        total_matches += len(rows)
                        console.print(f"  ✅ Found {len(rows)} matches in {table_name}", style="green")
                    else:
                        console.print(f"  ⚪ No matches in {table_name}", style="dim")

                except Exception as table_error:
                    console.print(f"  ❌ Error searching table {table_name}: {table_error}", style="red")
                    continue

        console.print(f"\n📊 Search Complete: {total_matches} total matches found across {len(session.search_results)} tables", style="bold green")

        # Initialize selected rows (all rows selected by default)
        session.selected_rows = {}
        for table_name, rows in session.search_results.items():
            try:
                # Assume first column is the primary key
                columns = inspector.get_columns(table_name)
                if columns:
                    pk_column = columns[0]['name']  # Usually 'id'
                    session.selected_rows[table_name] = [getattr(row, pk_column) for row in rows]
                else:
                    console.print(f"  ⚠️  Could not initialize row selection for {table_name}: no columns", style="yellow")
            except Exception as row_error:
                console.print(f"  ⚠️  Could not initialize row selection for {table_name}: {row_error}", style="yellow")

    except Exception as e:
        import traceback
        console.print(f"❌ Error during search: {str(e)}", style="bold red")
        console.print(f"❌ Error details: {traceback.format_exc()}", style="red")

def _preview_matches(session: SearchReplaceSession):
    """Preview the matches found in search results"""
    if not session.search_results:
        console.print("❌ No search results available! Run 'Find Matches' first.", style="bold red")
        return

    console.print(f"\n📋 Preview of matches for '{session.search_term}'", style="bold blue")

    total_matches = sum(len(rows) for rows in session.search_results.values())
    console.print(f"📊 Total: {total_matches} matches across {len(session.search_results)} tables", style="bold green")
    console.print()

    # Show preview for each table
    for table_name, rows in session.search_results.items():
        console.print(f"🗂️  Table: {table_name} ({len(rows)} matches)", style="bold cyan")

        # Show preview of matches with highlighted search terms
        _show_table_matches_preview(table_name, rows, session.search_term)
        console.print()

    console.print("💡 Use 'Configure Row Selection' to choose specific rows for replacement", style="dim")

def _configure_row_selection(session: SearchReplaceSession):
    """Allow user to configure which specific rows to modify"""
    if not session.search_results:
        console.print("❌ No search results available!", style="bold red")
        return

    for table_name, rows in session.search_results.items():
        console.print(f"\n📋 Configuring row selection for table: {table_name}", style="bold blue")
        console.print(f"Found {len(rows)} rows with matches", style="dim")

        # Show preview of matches with highlighted search terms
        _show_table_matches_preview(table_name, rows, session.search_term)

        # Ask user if they want to modify selection for this table
        questions = [
            inquirer.List(
                "action",
                message=f"Row selection for {table_name}",
                choices=[
                    "Keep all rows selected",
                    "Deselect specific rows",
                    "Select only specific rows",
                    "Skip this table entirely"
                ]
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            continue

        action = answers["action"]

        if action == "Skip this table entirely":
            session.selected_rows[table_name] = []
        elif action == "Deselect specific rows":
            _deselect_specific_rows(session, table_name, rows)
        elif action == "Select only specific rows":
            _select_only_specific_rows(session, table_name, rows)
        # "Keep all rows selected" requires no action

def _show_table_matches_preview(table_name: str, rows: List, search_term: str):
    """Show a preview of matches in a table with highlighted search terms"""
    if not rows:
        return

    # Get column names from first row
    all_columns = list(rows[0]._mapping.keys())

    # Find the primary key column (usually first column, typically 'id')
    pk_column = all_columns[0]

    # Find columns that contain the search term in any row
    matching_columns = set()
    for row in rows:
        for col_name in all_columns:
            value = getattr(row, col_name, '')
            if value and search_term.lower() in str(value).lower():
                matching_columns.add(col_name)

    # Create preview columns: ID + columns with matches
    preview_columns = [pk_column]
    for col in all_columns:
        if col != pk_column and col in matching_columns:
            preview_columns.append(col)

    # Create a preview table with full width
    match_count = len(matching_columns)
    console_width = console.size.width

    preview_table = Table(
        title=f"🔍 Matches in {table_name} - {match_count} column(s) with matches (showing first 10 rows)",
        expand=True,  # Use full terminal width
        show_lines=True,  # Add lines between rows for better readability
        width=console_width
    )

    # Calculate optimal column widths
    pk_width = 10  # Fixed width for primary key
    border_padding = len(preview_columns) * 3  # Account for borders and padding
    remaining_width = console_width - pk_width - border_padding
    content_width_per_col = max(30, remaining_width // max(1, len(preview_columns) - 1)) if len(preview_columns) > 1 else remaining_width

    # Add columns to the table with optimized widths
    for col in preview_columns:
        if col == pk_column:
            preview_table.add_column(col, style="cyan", width=pk_width, no_wrap=True)
        else:
            preview_table.add_column(
                col,
                overflow="fold",
                width=content_width_per_col,
                max_width=content_width_per_col
            )

    # Show first 10 rows with highlighted search terms
    for i, row in enumerate(rows[:10]):
        row_data = []
        for col in preview_columns:
            value = str(getattr(row, col, ''))

            if col == pk_column:
                # Show ID column without highlighting
                row_data.append(value)
            elif search_term.lower() in value.lower():
                # Create snippet showing context around the search term
                snippet_with_highlight = _create_highlighted_snippet(value, search_term, max_length=80)
                row_data.append(snippet_with_highlight)
            else:
                # This shouldn't happen since we only show matching columns
                display_value = value[:40] + "..." if len(value) > 40 else value
                row_data.append(display_value)

        preview_table.add_row(*row_data)

    if len(rows) > 10:
        preview_table.add_row(*["..." for _ in preview_columns])
        preview_table.add_row(*[f"({len(rows) - 10} more rows)" for _ in range(len(preview_columns))])

    console.print(preview_table)

    # Show summary of columns with matches
    if len(matching_columns) > 1:
        console.print(f"📋 Columns containing '{search_term}': {', '.join(sorted(matching_columns))}", style="dim")

def _create_highlighted_snippet(value: str, search_term: str, max_length: int = 80) -> Text:
    """Create a snippet showing context around the search term with highlighting"""
    from rich.text import Text

    value_lower = value.lower()
    search_lower = search_term.lower()

    # Find the first occurrence of the search term
    search_pos = value_lower.find(search_lower)
    if search_pos == -1:
        # Fallback: just truncate the value
        return Text(value[:max_length] + ("..." if len(value) > max_length else ""))

    # Calculate snippet boundaries to center around the search term
    search_end = search_pos + len(search_term)
    context_before = max_length // 3  # Show about 1/3 of space before the term
    context_after = max_length - context_before - len(search_term)  # Rest after the term

    # Calculate start and end positions
    snippet_start = max(0, search_pos - context_before)
    snippet_end = min(len(value), search_end + context_after)

    # Adjust if we're at the beginning or end
    if snippet_start == 0:
        snippet_end = min(len(value), max_length)
    elif snippet_end == len(value):
        snippet_start = max(0, len(value) - max_length)

    # Extract the snippet
    snippet = value[snippet_start:snippet_end]

    # Add ellipsis indicators
    prefix = "..." if snippet_start > 0 else ""
    suffix = "..." if snippet_end < len(value) else ""
    full_snippet = prefix + snippet + suffix

    # Create highlighted text
    highlighted = Text()

    # Add prefix ellipsis
    if prefix:
        highlighted.append(prefix, style="dim")

    # Find and highlight all occurrences of the search term in the snippet
    snippet_lower = snippet.lower()
    start = 0

    while True:
        pos = snippet_lower.find(search_lower, start)
        if pos == -1:
            # Add remaining text
            highlighted.append(snippet[start:])
            break

        # Add text before match
        highlighted.append(snippet[start:pos])
        # Add highlighted match
        highlighted.append(snippet[pos:pos + len(search_term)], style="bold red")
        start = pos + len(search_term)

    # Add suffix ellipsis
    if suffix:
        highlighted.append(suffix, style="dim")

    return highlighted

def _deselect_specific_rows(session: SearchReplaceSession, table_name: str, rows: List):
    """Allow user to deselect specific rows"""
    # Get primary key column
    columns = inspector.get_columns(table_name)
    pk_column = columns[0]['name']

    # Create choices for row selection
    choices = []
    for row in rows:
        pk_value = getattr(row, pk_column)
        # Create a summary of the row for display
        row_summary = _create_row_summary(row, session.search_term)
        choices.append(f"ID {pk_value}: {row_summary}")

    questions = [
        inquirer.Checkbox(
            "deselect_rows",
            message="Select rows to EXCLUDE from replacement (use SPACE to select, ENTER to confirm)",
            choices=choices
        )
    ]

    answers = inquirer.prompt(questions)
    if not answers:
        return

    # Extract IDs from deselected choices
    deselected_ids = []
    for choice in answers["deselect_rows"]:
        id_part = choice.split(":")[0].replace("ID ", "")
        try:
            deselected_ids.append(int(id_part))
        except ValueError:
            deselected_ids.append(id_part)

    # Update selected rows (remove deselected ones)
    current_selected = session.selected_rows.get(table_name, [])
    session.selected_rows[table_name] = [row_id for row_id in current_selected if row_id not in deselected_ids]

    console.print(f"✅ {len(deselected_ids)} rows deselected. {len(session.selected_rows[table_name])} rows will be modified.", style="green")

def _select_only_specific_rows(session: SearchReplaceSession, table_name: str, rows: List):
    """Allow user to select only specific rows"""
    # Get primary key column
    columns = inspector.get_columns(table_name)
    pk_column = columns[0]['name']

    # Create choices for row selection
    choices = []
    for row in rows:
        pk_value = getattr(row, pk_column)
        # Create a summary of the row for display
        row_summary = _create_row_summary(row, session.search_term)
        choices.append(f"ID {pk_value}: {row_summary}")

    questions = [
        inquirer.Checkbox(
            "select_rows",
            message="Select rows to INCLUDE in replacement (use SPACE to select, ENTER to confirm)",
            choices=choices
        )
    ]

    answers = inquirer.prompt(questions)
    if not answers:
        session.selected_rows[table_name] = []
        return

    # Extract IDs from selected choices
    selected_ids = []
    for choice in answers["select_rows"]:
        id_part = choice.split(":")[0].replace("ID ", "")
        try:
            selected_ids.append(int(id_part))
        except ValueError:
            selected_ids.append(id_part)

    session.selected_rows[table_name] = selected_ids
    console.print(f"✅ {len(selected_ids)} rows selected for modification.", style="green")

def _create_row_summary(row, search_term: str) -> str:
    """Create a summary of a row for display purposes"""
    # Get all column values and find those containing the search term
    matching_parts = []
    for key, value in row._mapping.items():
        if value and search_term.lower() in str(value).lower():
            # Get a snippet around the search term
            value_str = str(value)
            search_pos = value_str.lower().find(search_term.lower())
            start = max(0, search_pos - 15)
            end = min(len(value_str), search_pos + len(search_term) + 15)
            snippet = value_str[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(value_str):
                snippet = snippet + "..."
            # Clean up snippet for display
            snippet = snippet.replace('\n', ' ').replace('\r', ' ')
            matching_parts.append(f"{key}: {snippet}")

    return " | ".join(matching_parts[:3])  # Show first 3 matching parts

def _get_replace_term(session: SearchReplaceSession) -> bool:
    """Get the replacement text from user"""
    questions = [
        inquirer.Text(
            "replace_term",
            message="Enter the replacement text",
            default=session.replace_term
        )
    ]

    answers = inquirer.prompt(questions)
    if answers is None:
        return False

    session.replace_term = answers["replace_term"]
    return True

def _execute_replace(session: SearchReplaceSession, dry_run: bool = True):
    """Execute the search and replace operation"""
    if not session.search_results:
        console.print("❌ No search results available!", style="bold red")
        return

    if not session.replace_term and session.replace_term != "":
        console.print("❌ No replacement text specified!", style="bold red")
        return

    # Calculate total operations
    total_operations = sum(len(row_ids) for row_ids in session.selected_rows.values())

    if total_operations == 0:
        console.print("❌ No rows selected for modification!", style="bold red")
        return

    # Show summary
    console.print(f"\n📊 {'DRY RUN - ' if dry_run else ''}Search and Replace Summary:", style="bold blue")
    console.print(f"  Search Term: '{session.search_term}'", style="dim")
    console.print(f"  Replace With: '{session.replace_term}'", style="dim")
    console.print(f"  Total Operations: {total_operations}", style="dim")

    summary_table = Table(
        title="Tables and Rows to Modify",
        expand=True,  # Use full terminal width
        show_lines=True
    )
    summary_table.add_column("Table", style="cyan", width=40)
    summary_table.add_column("Rows Selected", style="green", justify="center", width=15)
    summary_table.add_column("Total Matches", style="yellow", justify="center", width=15)

    for table_name in session.search_results.keys():
        selected_count = len(session.selected_rows.get(table_name, []))
        total_count = len(session.search_results[table_name])
        summary_table.add_row(table_name, str(selected_count), str(total_count))

    console.print(summary_table)

    if not dry_run:
        # Final confirmation
        console.print("\n⚠️  WARNING: This operation will modify your database!", style="bold red")
        questions = [
            inquirer.Confirm(
                "confirm",
                message="Are you absolutely sure you want to proceed?",
                default=False
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers or not answers["confirm"]:
            console.print("❌ Operation cancelled by user.", style="yellow")
            return

        # Create backup file
        session.create_backup_file()
        console.print(f"📁 Backup file created: {session.backup_file}", style="green")

    # Execute the replacement
    try:
        with engine.connect() as connection:
            transaction = connection.begin()

            try:
                changes_made = []

                for table_name, row_ids in session.selected_rows.items():
                    if not row_ids:
                        continue

                    console.print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing table: {table_name}", style="bold")

                    # Get table columns with better error handling
                    try:
                        columns = inspector.get_columns(table_name)
                        if not columns:
                            console.print(f"  ⚠️  No columns found in {table_name}, skipping", style="yellow")
                            continue
                        pk_column = columns[0]['name']

                        # Find text columns with safer type checking
                        text_columns = []
                        for col in columns:
                            try:
                                col_type_str = str(col['type']).upper()
                                if any(text_type in col_type_str for text_type in ['TEXT', 'VARCHAR', 'CHAR', 'LONGTEXT', 'MEDIUMTEXT', 'TINYTEXT']):
                                    text_columns.append(col['name'])
                                elif hasattr(col['type'], 'python_type'):
                                    if col['type'].python_type in (str, type(None)):
                                        text_columns.append(col['name'])
                            except Exception:
                                # If we can't determine the type, include it anyway
                                text_columns.append(col['name'])

                    except Exception as col_error:
                        console.print(f"  ❌ Error getting columns for {table_name}: {col_error}", style="red")
                        continue

                    for row_id in row_ids:
                        # Get current row data
                        select_query = text(f"SELECT * FROM `{table_name}` WHERE `{pk_column}` = :row_id")
                        result = connection.execute(select_query, {"row_id": row_id})
                        row = result.fetchone()

                        if not row:
                            console.print(f"  ⚠️  Row {row_id} not found, skipping", style="yellow")
                            continue

                        # Process each text column
                        updates = {}
                        row_changes = []

                        for col_name in text_columns:
                            original_value = getattr(row, col_name)
                            if original_value and session.search_term in str(original_value):
                                # Handle serialized data safely
                                new_value = _safe_replace_in_serialized_data(
                                    str(original_value),
                                    session.search_term,
                                    session.replace_term
                                )

                                if new_value != original_value:
                                    updates[col_name] = new_value
                                    row_changes.append({
                                        "table": table_name,
                                        "row_id": row_id,
                                        "column": col_name,
                                        "original_value": original_value,
                                        "new_value": new_value
                                    })

                        # Execute updates
                        if updates and not dry_run:
                            update_parts = [f"`{col}` = :{col}" for col in updates.keys()]
                            update_query = text(f"UPDATE `{table_name}` SET {', '.join(update_parts)} WHERE `{pk_column}` = :row_id")

                            params = updates.copy()
                            params["row_id"] = row_id

                            connection.execute(update_query, params)
                            changes_made.extend(row_changes)

                        if updates:
                            console.print(f"  ✅ {'Would update' if dry_run else 'Updated'} row {row_id} ({len(updates)} columns)", style="green")
                        else:
                            console.print(f"  ⚪ No changes needed for row {row_id}", style="dim")

                if not dry_run:
                    # Save changes to backup file
                    if session.backup_file and changes_made:
                        with open(session.backup_file, 'r') as f:
                            backup_data = json.load(f)

                        backup_data["changes"] = changes_made

                        with open(session.backup_file, 'w') as f:
                            json.dump(backup_data, f, indent=2)

                    transaction.commit()
                    console.print(f"\n✅ Search and replace completed! {len(changes_made)} changes made.", style="bold green")
                    session.changes_made = changes_made
                else:
                    transaction.rollback()
                    console.print(f"\n✅ Dry run completed! {sum(len(session.selected_rows.get(table, [])) for table in session.search_results.keys())} rows would be modified.", style="bold green")

            except Exception as e:
                transaction.rollback()
                raise e

    except Exception as e:
        console.print(f"❌ Error during {'dry run' if dry_run else 'replacement'}: {e}", style="bold red")

def _safe_replace_in_serialized_data(original_value: str, search_term: str, replace_term: str) -> str:
    """Safely replace text in potentially serialized data"""

    # Handle None or empty values
    if not original_value:
        return original_value or ""

    # Convert to string if not already
    original_value = str(original_value)

    # Check if this looks like PHP serialized data
    if _is_php_serialized(original_value):
        return _replace_in_php_serialized(original_value, search_term, replace_term)

    # Check if this looks like JSON
    if _is_json_data(original_value):
        return _replace_in_json_data(original_value, search_term, replace_term)

    # For regular strings, do simple replacement
    return original_value.replace(search_term, replace_term)

def _is_php_serialized(value: str) -> bool:
    """Check if a string looks like PHP serialized data"""
    if not value:
        return False

    # PHP serialized data patterns
    patterns = [
        r'^a:\d+:\{.*\}$',  # array
        r'^s:\d+:".*";$',   # string
        r'^i:\d+;$',        # integer
        r'^b:[01];$',       # boolean
        r'^O:\d+:".*":\d+:\{.*\}$',  # object
    ]

    for pattern in patterns:
        if re.match(pattern, value, re.DOTALL):
            return True

    return False

def _is_json_data(value: str) -> bool:
    """Check if a string looks like JSON data"""
    if not value:
        return False

    try:
        json.loads(value)
        return True
    except (json.JSONDecodeError, ValueError):
        return False

def _replace_in_php_serialized(serialized_data: str, search_term: str, replace_term: str) -> str:
    """Safely replace text in PHP serialized data"""
    try:
        # For PHP serialized data, we need to be very careful
        # We'll do a simple string replacement but then validate the result

        # First, try simple replacement
        new_data = serialized_data.replace(search_term, replace_term)

        # If the replacement changed the length of strings, we need to update the length indicators
        if search_term != replace_term and len(search_term) != len(replace_term):
            new_data = _fix_php_serialized_lengths(new_data)

        return new_data

    except Exception:
        # If anything goes wrong, return original data
        console.print("⚠️  Warning: Could not safely replace in serialized data, skipping", style="yellow")
        return serialized_data

def _fix_php_serialized_lengths(serialized_data: str) -> str:
    """Fix string length indicators in PHP serialized data"""
    def replace_string_length(match):
        length_str = match.group(1)
        content = match.group(2)
        # Use character length, not byte length for simplicity
        actual_length = len(content)
        return f's:{actual_length}:"{content}";'

    # Pattern to match s:length:"content"; in PHP serialized data
    pattern = r's:(\d+):"([^"]*)";'
    return re.sub(pattern, replace_string_length, serialized_data)

def _replace_in_json_data(json_data: str, search_term: str, replace_term: str) -> str:
    """Safely replace text in JSON data"""
    try:
        # Parse JSON, replace in string values, and re-serialize
        data = json.loads(json_data)
        modified_data = _replace_in_json_object(data, search_term, replace_term)
        return json.dumps(modified_data, ensure_ascii=False)
    except Exception:
        # If anything goes wrong, fall back to simple replacement
        return json_data.replace(search_term, replace_term)

def _replace_in_json_object(obj, search_term: str, replace_term: str):
    """Recursively replace text in JSON object"""
    if isinstance(obj, dict):
        return {key: _replace_in_json_object(value, search_term, replace_term) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_replace_in_json_object(item, search_term, replace_term) for item in obj]
    elif isinstance(obj, str):
        return obj.replace(search_term, replace_term)
    else:
        return obj

def _undo_last_operation():
    """Undo the last search and replace operation"""
    # Get list of backup files
    backup_files = list(BACKUPS_DIR.glob("search_replace_backup_*.json"))

    if not backup_files:
        console.print("❌ No backup files found!", style="bold red")
        return

    # Sort by modification time (newest first)
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Show available backups
    choices = []
    for backup_file in backup_files[:10]:  # Show last 10 backups
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)

        timestamp = backup_data.get("timestamp", "Unknown")
        search_term = backup_data.get("search_term", "Unknown")
        changes_count = len(backup_data.get("changes", []))

        choices.append(f"{timestamp} - Search: '{search_term}' ({changes_count} changes)")

    choices.append("Cancel")

    questions = [
        inquirer.List(
            "backup_choice",
            message="Select backup to restore",
            choices=choices
        )
    ]

    answers = inquirer.prompt(questions)
    if not answers or answers["backup_choice"] == "Cancel":
        return

    # Get selected backup file
    selected_index = choices.index(answers["backup_choice"])
    if selected_index >= len(backup_files):
        return

    backup_file = backup_files[selected_index]

    # Load backup data
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)

    changes = backup_data.get("changes", [])

    if not changes:
        console.print("❌ No changes found in backup file!", style="bold red")
        return

    # Show confirmation
    console.print(f"\n📊 Undo Operation Summary:", style="bold blue")
    console.print(f"  Backup File: {backup_file.name}", style="dim")
    console.print(f"  Original Search: '{backup_data.get('search_term', 'Unknown')}'", style="dim")
    console.print(f"  Changes to Undo: {len(changes)}", style="dim")

    questions = [
        inquirer.Confirm(
            "confirm_undo",
            message="Are you sure you want to undo these changes?",
            default=False
        )
    ]

    answers = inquirer.prompt(questions)
    if not answers or not answers["confirm_undo"]:
        console.print("❌ Undo operation cancelled.", style="yellow")
        return

    # Execute undo
    try:
        with engine.connect() as connection:
            transaction = connection.begin()

            try:
                undone_count = 0

                for change in changes:
                    table_name = change["table"]
                    row_id = change["row_id"]
                    column = change["column"]
                    original_value = change["original_value"]

                    # Get primary key column name
                    columns = inspector.get_columns(table_name)
                    pk_column = columns[0]['name']

                    # Restore original value
                    update_query = text(f"UPDATE `{table_name}` SET `{column}` = :original_value WHERE `{pk_column}` = :row_id")
                    connection.execute(update_query, {
                        "original_value": original_value,
                        "row_id": row_id
                    })

                    undone_count += 1
                    console.print(f"  ✅ Restored {table_name}.{column} for row {row_id}", style="green")

                transaction.commit()
                console.print(f"\n✅ Undo completed! {undone_count} changes restored.", style="bold green")

                # Mark backup file as used
                backup_file.rename(backup_file.with_suffix('.json.used'))

            except Exception as e:
                transaction.rollback()
                raise e

    except Exception as e:
        console.print(f"❌ Error during undo operation: {e}", style="bold red")

import os
import inquirer
import datetime
from rich.console import Console
from rich.table import Table
from sqlalchemy import inspect
from sqlalchemy.sql import text
from dotenv import load_dotenv

from src.db_utils import get_db_engine, get_db_inspector, check_db_connection_with_friendly_error

console = Console()

# Ensure environment variables are loaded
load_dotenv(override=True)

# Global variables for lazy database connection
engine = None
inspector = None
table_prefix = os.getenv('TABLE_PREFIX', '')

def get_engine():
    """Get database engine with error handling."""
    global engine
    if engine is None:
        if not check_db_connection_with_friendly_error():
            raise Exception("Database connection failed")
        engine = get_db_engine()
    return engine

def get_inspector():
    """Get database inspector with error handling."""
    global inspector
    if inspector is None:
        if not check_db_connection_with_friendly_error():
            raise Exception("Database connection failed")
        inspector = get_db_inspector()
    return inspector

# Common table names
users_table = f"{table_prefix}users"
usermeta_table = f"{table_prefix}usermeta"
posts_table = f"{table_prefix}posts"
postmeta_table = f"{table_prefix}postmeta"

def search_database():
    """Main search menu function"""
    questions = [
        inquirer.List(
            "search_option",
            message="🔍 Select search type",
            choices=[
                "1. Search Users", 
                "2. Search Orders", 
                "3. Search Coupons", 
                "4. Search Posts",
                "5. Search Pages",
                "6. Search Custom Post Type",
                "7. General Search", 
                "Back"
            ],
        )
    ]
    answers = inquirer.prompt(questions)
    
    if answers["search_option"] == "1. Search Users":
        search_users()
    elif answers["search_option"] == "2. Search Orders":
        search_orders()
    elif answers["search_option"] == "3. Search Coupons":
        search_coupons()
    elif answers["search_option"] == "4. Search Posts":
        search_regular_posts()
    elif answers["search_option"] == "5. Search Pages":
        search_posts(post_type="page", display_name="Page")
    elif answers["search_option"] == "6. Search Custom Post Type":
        search_custom_post_type()
    elif answers["search_option"] == "7. General Search":
        general_search()
    elif answers["search_option"] == "Back":
        return

def search_users(export_mode=False):
    """
    Search specifically in the users table
    
    Parameters:
    export_mode (bool): If True, returns the SQL query, params, and metadata for export instead of displaying results
    
    Returns:
    If export_mode is True, returns a tuple of (query, params, meta_info)
    """
    try:
        # Check if tables exist
        if users_table not in get_inspector().get_table_names():
            console.print(f"❌ Table {users_table} not found!", style="bold red")
            return None if export_mode else None

        if usermeta_table not in get_inspector().get_table_names():
            console.print(f"❌ Table {usermeta_table} not found!", style="bold red")
            return None if export_mode else None
        
        # Ask user which type of search they want to perform
        search_type_questions = [
            inquirer.List(
                "search_type",
                message="🔍 Select search type",
                choices=[
                    "1. Search by user fields",
                    "2. Search by user meta data",
                    "Back"
                ],
            )
        ]
        
        search_type_answers = inquirer.prompt(search_type_questions)
        search_type = search_type_answers["search_type"]
        
        if search_type == "Back":
            return None if export_mode else None
            
        # We'll collect selected meta keys for export later
        selected_export_meta_keys = []
        
        if search_type == "1. Search by user fields":
            # Ask which field to filter by
            field_questions = [
                inquirer.List(
                    "filter_field",
                    message="Select field to filter by",
                    choices=[
                        "All fields (general search)",
                        "ID",
                        "user_login", 
                        "user_email",
                        "user_registered",
                        "Back"
                    ],
                )
            ]
            
            field_answers = inquirer.prompt(field_questions)
            filter_field = field_answers["filter_field"]
            
            if filter_field == "Back":
                return None if export_mode else None

            # Build WHERE clause based on selected field
            if filter_field == "All fields (general search)":
                # Get column names
                columns_info = get_inspector().get_columns(users_table)
                column_names = [col['name'] for col in columns_info]
                
                # Original behavior - search all fields
                search_term = console.input("[bold blue]🔍 Enter search term for users: [/bold blue]")
                where_conditions = []
                for col in column_names:
                    where_conditions.append(f"`{col}` LIKE :search_term")
                
                where_clause = " OR ".join(where_conditions)
                params = {"search_term": f"%{search_term}%"}
                
            elif filter_field in ["user_login", "user_email", "ID"]:
                match_type = _get_match_type(filter_field)
                if match_type == "Back":
                    return None if export_mode else None
                    
                value = console.input(f"[bold blue]🔍 Enter {filter_field}: [/bold blue]")
                
                if match_type == "Exact match":
                    where_clause = f"{filter_field} = :term"
                    params = {"term": value}
                elif match_type == "Contains":  # Contains
                    where_clause = f"{filter_field} LIKE :term"
                    params = {"term": f"%{value}%"}
                elif match_type == "In list (comma separated)":
                    # Split by comma and remove whitespace
                    values = [v.strip() for v in value.split(",")]
                    if not values:
                        console.print("❌ No valid values provided.", style="bold red")
                        return None if export_mode else None
                    
                    # Build IN clause parameters
                    in_clause_params = {}
                    in_clause_list = []
                    for i, val in enumerate(values):
                        param_name = f"term_{i}"
                        in_clause_params[param_name] = val
                        in_clause_list.append(f":{param_name}")
                    
                    where_clause = f"{filter_field} IN ({', '.join(in_clause_list)})"
                    params = in_clause_params
            
            elif filter_field == "user_registered":
                # Ask if the user wants to filter by date range
                date_range_questions = [
                    inquirer.List(
                        "date_range",
                        message="Do you want to filter by a date range?",
                        choices=["Yes", "No (just from date)", "Back"],
                    )
                ]
                
                date_range_answers = inquirer.prompt(date_range_questions)
                date_range_option = date_range_answers["date_range"]
                
                if date_range_option == "Back":
                    return None if export_mode else None
                
                # Get the from date
                from_date_str = console.input("[bold blue]🔍 Enter from date (YYYY-MM-DD) to find users registered after: [/bold blue]")
                try:
                    # Validate from date format
                    datetime.datetime.strptime(from_date_str, "%Y-%m-%d")
                    
                    if date_range_option == "Yes":
                        # Also get the to date
                        to_date_str = console.input("[bold blue]🔍 Enter to date (YYYY-MM-DD) or leave empty: [/bold blue]")
                        if to_date_str.strip():
                            # Validate to date format
                            datetime.datetime.strptime(to_date_str, "%Y-%m-%d")
                            where_clause = "user_registered >= :from_date AND user_registered <= :to_date"
                            params = {"from_date": from_date_str, "to_date": to_date_str}
                        else:
                            # Only from date
                            where_clause = "user_registered >= :from_date"
                            params = {"from_date": from_date_str}
                    else:
                        # Just use from date
                        where_clause = "user_registered >= :from_date"
                        params = {"from_date": from_date_str}
                        
                except ValueError:
                    console.print("❌ Invalid date format. Please use YYYY-MM-DD format.", style="bold red")
                    return None if export_mode else None
            
            # Execute search
            with get_engine().connect() as connection:
                # Count query
                count_sql = text(f"SELECT COUNT(*) FROM `{users_table}` WHERE {where_clause}")
                count_result = connection.execute(count_sql, params)
                count = count_result.scalar()
                
                if count == 0:
                    console.print("⚠️ No matching users found.", style="bold yellow")
                    return None if export_mode else None
                
                console.print(f"✅ Found {count} matching users", style="bold green")
                
                # If in export mode, ask which meta keys to include AFTER search is done
                if export_mode and count > 0:
                    # First get all available meta keys
                    all_meta_keys_sql = text(f"SELECT DISTINCT meta_key FROM `{usermeta_table}` ORDER BY meta_key LIMIT 500")
                    all_meta_keys_result = connection.execute(all_meta_keys_sql)
                    all_meta_keys = [row[0] for row in all_meta_keys_result]
                    
                    # Ask user to select which meta keys to include in export
                    if all_meta_keys:
                        meta_key_choices = [(meta_key, meta_key) for meta_key in all_meta_keys]
                        
                        console.print("Select which user meta keys to include in the export:", style="bold blue")
                        meta_key_questions = [
                            inquirer.Checkbox(
                                "selected_meta_keys",
                                message="Press space to select/deselect keys, Enter when done",
                                choices=meta_key_choices,
                            )
                        ]
                        
                        meta_key_answers = inquirer.prompt(meta_key_questions)
                        selected_export_meta_keys = meta_key_answers["selected_meta_keys"]
                        
                        if selected_export_meta_keys:
                            console.print(f"✅ Will export {len(selected_export_meta_keys)} meta keys for each user", style="bold green")
                
                    query = f"SELECT * FROM `{users_table}` WHERE {where_clause}"
                    
                    return (query, params, {
                        "count": count, 
                        "table": users_table, 
                        "is_meta": False,
                        "export_meta_keys": selected_export_meta_keys,
                        "meta_table": usermeta_table
                    })
                
                # Get results for display
                select_sql = text(f"SELECT ID, user_login, user_email, user_registered, user_nicename, display_name FROM `{users_table}` WHERE {where_clause} LIMIT 100")
                result = connection.execute(select_sql, params)
                rows = result.fetchall()
                
                # Display results
                display_user_results(result.keys(), rows)
                return None
                
        elif search_type == "2. Search by user meta data":
            # Get meta key filter prefix from user
            meta_prefix = console.input("[bold blue]Enter prefix to filter meta keys (leave empty for all): [/bold blue]")
            
            # Get available meta keys from usermeta table with filter
            with get_engine().connect() as connection:
                if meta_prefix:
                    meta_keys_sql = text(f"SELECT DISTINCT meta_key FROM `{usermeta_table}` WHERE meta_key LIKE :prefix ORDER BY meta_key LIMIT 500")
                    meta_keys_result = connection.execute(meta_keys_sql, {"prefix": f"{meta_prefix}%"})
                else:
                    meta_keys_sql = text(f"SELECT DISTINCT meta_key FROM `{usermeta_table}` ORDER BY meta_key LIMIT 500")
                    meta_keys_result = connection.execute(meta_keys_sql)
                
                meta_keys = [row[0] for row in meta_keys_result]
            
            # Meta data search
            if not meta_keys:
                console.print("⚠️ No user meta keys found matching the prefix.", style="bold yellow")
                return None if export_mode else None
            
            console.print(f"✅ Found {len(meta_keys)} meta keys" + (f" starting with '{meta_prefix}'" if meta_prefix else ""), style="bold green")
                
                
            # Let user select a meta key for search
            meta_key_questions = [
                inquirer.List(
                    "meta_key",
                    message="Select a meta key to search by",
                    choices=meta_keys + ["Back"],
                )
            ]
            
            meta_key_answers = inquirer.prompt(meta_key_questions)
            selected_meta_key = meta_key_answers["meta_key"]
            
            if selected_meta_key == "Back":
                return None if export_mode else None
            
            # Show a sample value for the selected meta key
            with get_engine().connect() as connection:
                sample_sql = text(f"""
                    SELECT um.user_id, um.meta_value 
                    FROM `{usermeta_table}` um
                    WHERE um.meta_key = :meta_key
                    LIMIT 1
                """)
                
                sample_result = connection.execute(sample_sql, {"meta_key": selected_meta_key})
                sample_row = sample_result.fetchone()
                
                if sample_row:
                    user_id, meta_value = sample_row
                    # Format the output based on the meta value type and length
                    if meta_value is None:
                        formatted_value = "NULL"
                    elif len(str(meta_value)) > 100:
                        formatted_value = f"{str(meta_value)[:100]}... (truncated)"
                    else:
                        formatted_value = str(meta_value)
                    
                    console.print(f"📝 Sample value for '{selected_meta_key}':", style="bold cyan")
                    console.print(f"User ID: {user_id}", style="cyan")
                    console.print(f"Value: {formatted_value}", style="cyan")
                    console.print("")  # Add a blank line for better readability
                
            # Get search term and match type
            match_type = _get_match_type(f"'{selected_meta_key}' value")
            if match_type == "Back":
                return None if export_mode else None
            
            search_term = console.input(f"[bold blue]🔍 Enter search term for {selected_meta_key}: [/bold blue]")
            
            # Build the WHERE clause based on match type
            if match_type == "Exact match":
                meta_where_clause = "um.meta_value = :search_term"
                params = {"meta_key": selected_meta_key, "search_term": search_term}
            elif match_type == "Contains":  # Contains
                meta_where_clause = "um.meta_value LIKE :search_term"
                params = {"meta_key": selected_meta_key, "search_term": f"%{search_term}%"}
            elif match_type == "In list (comma separated)":
                # Split by comma and remove whitespace
                values = [v.strip() for v in search_term.split(",")]
                if not values:
                    console.print("❌ No valid values provided.", style="bold red")
                    return None if export_mode else None
                
                # Build IN clause parameters
                in_clause_params = {"meta_key": selected_meta_key}
                in_clause_list = []
                for i, val in enumerate(values):
                    param_name = f"term_{i}"
                    in_clause_params[param_name] = val
                    in_clause_list.append(f":{param_name}")
                
                meta_where_clause = f"um.meta_value IN ({', '.join(in_clause_list)})"
                params = in_clause_params
                
            # Execute the meta search query
            with get_engine().connect() as connection:
                # Join users and usermeta tables
                query = f"""
                    SELECT {'u.*' if export_mode else 'u.ID, u.user_login, u.user_email, u.user_registered, u.user_nicename, u.display_name'}
                    FROM `{users_table}` u
                    INNER JOIN `{usermeta_table}` um ON u.ID = um.user_id
                    WHERE um.meta_key = :meta_key
                    AND {meta_where_clause}
                """
                
                # If in export mode, return the query and params
                if export_mode:
                    
                    # If in export mode, ask which filtered meta keys to include in the export
                    # First get all available meta keys
                    all_meta_keys_sql = text(f"SELECT DISTINCT meta_key FROM `{usermeta_table}` ORDER BY meta_key LIMIT 500")
                    all_meta_keys_result = connection.execute(all_meta_keys_sql)
                    all_meta_keys = [row[0] for row in all_meta_keys_result]
                    
                    # Ask user to select which meta keys to include in export
                    if all_meta_keys:
                        meta_key_choices = [(meta_key, meta_key) for meta_key in all_meta_keys]
                        
                        console.print("Select which user meta keys to include in the export:", style="bold blue")
                        meta_key_questions = [
                            inquirer.Checkbox(
                                "selected_meta_keys",
                                message="Press space to select/deselect keys, Enter when done",
                                choices=meta_key_choices,
                            )
                        ]
                        
                        meta_key_answers = inquirer.prompt(meta_key_questions)
                        selected_export_meta_keys = meta_key_answers["selected_meta_keys"]
                        
                        if selected_export_meta_keys:
                            console.print(f"✅ Will export {len(selected_export_meta_keys)} meta keys for each user", style="bold green")
                    
                    # if export_mode:
                    #     meta_key_choices = [(meta_key, meta_key) for meta_key in meta_keys]
                        
                    #     console.print("Select which user meta keys to include in the export:", style="bold blue")
                    #     meta_key_questions = [
                    #         inquirer.Checkbox(
                    #             "selected_meta_keys",
                    #             message="Press space to select/deselect keys, Enter when done",
                    #             choices=meta_key_choices,
                    #         )
                    #     ]
                        
                    #     meta_key_answers = inquirer.prompt(meta_key_questions)
                    #     selected_export_meta_keys = meta_key_answers["selected_meta_keys"]
                        
                    #     if selected_export_meta_keys:
                    #         console.print(f"✅ Will export {len(selected_export_meta_keys)} meta keys for each user", style="bold green")

                    count_sql = text(f"""
                        SELECT COUNT(DISTINCT u.ID) 
                        FROM `{users_table}` u
                        INNER JOIN `{usermeta_table}` um ON u.ID = um.user_id
                        WHERE um.meta_key = :meta_key AND {meta_where_clause}
                    """)
                    count_result = connection.execute(count_sql, params)
                    count = count_result.scalar()
                    
                    if count == 0:
                        console.print("⚠️ No matching users found.", style="bold yellow")
                        return None
                        
                    console.print(f"✅ Found {count} matching users", style="bold green")
                    
                    return (
                        query, 
                        params, 
                        {
                            "count": count, 
                            "table": users_table, 
                            "meta_table": usermeta_table,
                            "meta_key": selected_meta_key,
                            "is_meta": True,
                            "export_meta_keys": selected_export_meta_keys
                        }
                    )
                
                # For regular search mode
                sql = text(query + " LIMIT 100")
                result = connection.execute(sql, params)
                rows = result.fetchall()
                count = len(rows)
                
                if count == 0:
                    console.print("⚠️ No matching users found.", style="bold yellow")
                    return None
                
                console.print(f"✅ Found {count} matching users", style="bold green")
                
                # Display results
                display_user_results(result.keys(), rows)
                return None
                
    except Exception as e:
        console.print(f"❌ User search failed: {e}", style="bold red")
        return None if export_mode else None

def _get_match_type(term_type):
    """Helper function to determine match type (exact or contains)"""
    match_questions = [
        inquirer.List(
            "match_type",
            message=f"👉 Select how to match {term_type}",
            choices=["Exact match", "Contains", "In list (comma separated)", "Back"],
        )
    ]
    
    match_answers = inquirer.prompt(match_questions)
    return match_answers["match_type"]

def display_user_results(column_names, rows):
    """Helper function to display user search results in a table"""
    results_table = Table(
        title=f"👤 User Search Results (showing up to 100 rows)",
        expand=True,  # Use full terminal width
        show_lines=True
    )

    # Calculate optimal column widths
    console_width = console.size.width
    col_width = max(20, (console_width - (len(column_names) * 3)) // len(column_names))

    # Add columns
    for column_name in column_names:
        results_table.add_column(column_name, overflow="fold", width=col_width, max_width=col_width)
    
    # Add rows
    for row in rows:
        string_values = [str(value) if value is not None else "" for value in row]
        results_table.add_row(*string_values)
    
    console.print(results_table)

def search_posts(post_type, export_mode=False, display_name=None):
    """
    Generic search function for any WordPress post type
    
    Parameters:
    post_type (str): The post type to search for (e.g. 'shop_order', 'shop_coupon', 'post')
    export_mode (bool): If True, returns the SQL query, params, and metadata for export
    display_name (str): Display name for the post type (e.g. "Order", "Coupon", "Post")
    
    Returns:
    If export_mode is True, returns a tuple of (query, params, meta_info)
    """
    if display_name is None:
        display_name = post_type.replace('_', ' ').title()
    
    icon = "🛒" if "order" in post_type else "🎟️" if "coupon" in post_type else "📄"
    
    try:
        # Check if tables exist
        if posts_table not in get_inspector().get_table_names():
            console.print(f"❌ Table {posts_table} not found!", style="bold red")
            return None if export_mode else None

        if postmeta_table not in get_inspector().get_table_names():
            console.print(f"❌ Table {postmeta_table} not found!", style="bold red")
            return None if export_mode else None
        
        # Ask user which type of search they want to perform
        search_type_questions = [
            inquirer.List(
                "search_type",
                message=f"🔍 Select {display_name.lower()} search type",
                choices=[
                    f"1. Search by {display_name.lower()} fields",
                    f"2. Search by {display_name.lower()} meta data",
                    "Back"
                ],
            )
        ]
        
        search_type_answers = inquirer.prompt(search_type_questions)
        search_type = search_type_answers["search_type"]
        
        if search_type == "Back":
            return None if export_mode else None
            
        # We'll collect selected meta keys for export later
        selected_export_meta_keys = []
        
        if search_type.startswith("1. Search by"):  # Search by post fields
            # Ask which field to filter by
            field_questions = [
                inquirer.List(
                    "filter_field",
                    message=f"Select field to filter by",
                    choices=[
                        "All fields (general search)",
                        "post_title", 
                        "post_status",
                        "post_date",
                        "post_modified",
                        "post_name",
                        "guid",
                        "post_author",
                        "post_content",
                        "ID",
                        "Back"
                    ],
                )
            ]
            
            field_answers = inquirer.prompt(field_questions)
            filter_field = field_answers["filter_field"]
            
            if filter_field == "Back":
                return None if export_mode else None

            # Build WHERE clause based on selected field
            base_condition = f"post_type = '{post_type}'"
            
            if filter_field == "All fields (general search)":
                # Get column names
                columns_info = get_inspector().get_columns(posts_table)
                column_names = [col['name'] for col in columns_info]
                
                # Search all fields
                search_term = console.input(f"[bold blue]🔍 Enter search term for {display_name.lower()}s: [/bold blue]")
                where_conditions = []
                for col in column_names:
                    where_conditions.append(f"`{col}` LIKE :search_term")
                
                field_where_clause = " OR ".join(where_conditions)
                where_clause = f"{base_condition} AND ({field_where_clause})"
                params = {"search_term": f"%{search_term}%"}
                
            elif filter_field in ["post_title", "post_status", "post_name", "guid", "post_author", "post_content"]:
                match_type = _get_match_type(filter_field)
                if match_type == "Back":
                    return None if export_mode else None
                    
                value = console.input(f"[bold blue]🔍 Enter {filter_field}: [/bold blue]")
                
                if match_type == "Exact match":
                    field_where_clause = f"{filter_field} = :term"
                    params = {"term": value}
                elif match_type == "Contains":  # Contains
                    field_where_clause = f"{filter_field} LIKE :term"
                    params = {"term": f"%{value}%"}
                elif match_type == "In list (comma separated)":
                    # Split by comma and remove whitespace
                    values = [v.strip() for v in value.split(",")]
                    if not values:
                        console.print("❌ No valid values provided.", style="bold red")
                        return None if export_mode else None
                    
                    # Build IN clause parameters
                    in_clause_params = {}
                    in_clause_list = []
                    for i, val in enumerate(values):
                        param_name = f"term_{i}"
                        in_clause_params[param_name] = val
                        in_clause_list.append(f":{param_name}")
                    
                    field_where_clause = f"{filter_field} IN ({', '.join(in_clause_list)})"
                    params = in_clause_params
                
                where_clause = f"{base_condition} AND ({field_where_clause})"
            
            elif filter_field == "ID":
                match_type = _get_match_type(filter_field)
                if match_type == "Back":
                    return None if export_mode else None
                
                if match_type == "In list (comma separated)":
                    value = console.input(f"[bold blue]🔍 Enter {filter_field} list (comma separated): [/bold blue]")
                    try:
                        # Split by comma, trim whitespace, and convert to integers
                        post_ids = [int(v.strip()) for v in value.split(",")]
                        if not post_ids:
                            console.print("❌ No valid IDs provided.", style="bold red")
                            return None if export_mode else None
                            
                        # Build IN clause parameters
                        in_clause_params = {}
                        in_clause_list = []
                        for i, post_id in enumerate(post_ids):
                            param_name = f"id_{i}"
                            in_clause_params[param_name] = post_id
                            in_clause_list.append(f":{param_name}")
                        
                        field_where_clause = f"ID IN ({', '.join(in_clause_list)})"
                        params = in_clause_params
                    except ValueError:
                        console.print("❌ Invalid ID format. Please enter numbers separated by commas.", style="bold red")
                        return None if export_mode else None
                else:
                    value = console.input(f"[bold blue]🔍 Enter {display_name.lower()} ID: [/bold blue]")
                    try:
                        post_id = int(value)
                        field_where_clause = "ID = :post_id"
                        params = {"post_id": post_id}
                    except ValueError:
                        console.print("❌ Invalid ID format. Please enter a number.", style="bold red")
                        return None if export_mode else None
                
                where_clause = f"{base_condition} AND ({field_where_clause})"
            
            elif filter_field in ["post_date", "post_modified"]:
                # Ask if the user wants to filter by date range
                date_range_questions = [
                    inquirer.List(
                        "date_range",
                        message=f"Do you want to filter {filter_field} by a date range?",
                        choices=["Yes", "No (just from date)", "Back"],
                    )
                ]
                
                date_range_answers = inquirer.prompt(date_range_questions)
                date_range_option = date_range_answers["date_range"]
                
                if date_range_option == "Back":
                    return None if export_mode else None
                
                # Get the from date
                from_date_str = console.input(f"[bold blue]🔍 Enter from date (YYYY-MM-DD) to find {display_name.lower()}s after: [/bold blue]")
                try:
                    # Validate from date format
                    datetime.datetime.strptime(from_date_str, "%Y-%m-%d")
                    
                    if date_range_option == "Yes":
                        # Also get the to date
                        to_date_str = console.input("[bold blue]🔍 Enter to date (YYYY-MM-DD) or leave empty: [/bold blue]")
                        if to_date_str.strip():
                            # Validate to date format
                            datetime.datetime.strptime(to_date_str, "%Y-%m-%d")
                            field_where_clause = f"{filter_field} >= :from_date AND {filter_field} <= :to_date"
                            params = {"from_date": from_date_str, "to_date": to_date_str}
                        else:
                            # Only from date
                            field_where_clause = f"{filter_field} >= :from_date"
                            params = {"from_date": from_date_str}
                    else:
                        # Just use from date
                        field_where_clause = f"{filter_field} >= :from_date"
                        params = {"from_date": from_date_str}
                    
                    where_clause = f"{base_condition} AND ({field_where_clause})"
                except ValueError:
                    console.print("❌ Invalid date format. Please use YYYY-MM-DD format.", style="bold red")
                    return None if export_mode else None
            
            # Execute search
            with get_engine().connect() as connection:
                # Count query
                count_sql = text(f"SELECT COUNT(*) FROM `{posts_table}` WHERE {where_clause}")
                count_result = connection.execute(count_sql, params)
                count = count_result.scalar()
                
                if count == 0:
                    console.print(f"⚠️ No matching {display_name.lower()}s found.", style="bold yellow")
                    return None if export_mode else None
                
                console.print(f"✅ Found {count} matching {display_name.lower()}s", style="bold green")
                
                # If in export mode, ask which meta keys to include AFTER search is done
                if export_mode and count > 0:
                    # First get all available meta keys for this post type
                    all_meta_keys_sql = text(f"""
                        SELECT DISTINCT meta_key FROM `{postmeta_table}` pm
                        JOIN `{posts_table}` p ON pm.post_id = p.ID
                        WHERE p.post_type = :post_type
                        ORDER BY meta_key 
                        LIMIT 500
                    """)
                    all_meta_keys_result = connection.execute(all_meta_keys_sql, {"post_type": post_type})
                    all_meta_keys = [row[0] for row in all_meta_keys_result]
                    
                    # Ask user to select which meta keys to include in export
                    if all_meta_keys:
                        meta_key_choices = [(meta_key, meta_key) for meta_key in all_meta_keys]
                        
                        console.print(f"Select which {display_name.lower()} meta keys to include in the export:", style="bold blue")
                        meta_key_questions = [
                            inquirer.Checkbox(
                                "selected_meta_keys",
                                message="Press space to select/deselect keys, Enter when done",
                                choices=meta_key_choices,
                            )
                        ]
                        
                        meta_key_answers = inquirer.prompt(meta_key_questions)
                        selected_export_meta_keys = meta_key_answers["selected_meta_keys"]
                        
                        if selected_export_meta_keys:
                            console.print(f"✅ Will export {len(selected_export_meta_keys)} meta keys for each {display_name.lower()}", style="bold green")
                
                    query = f"SELECT * FROM `{posts_table}` WHERE {where_clause}"
                    return (query, params, {
                        "count": count, 
                        "table": posts_table, 
                        "is_meta": False,
                        "export_meta_keys": selected_export_meta_keys,
                        "meta_table": postmeta_table,
                        "post_type": post_type,
                        "display_name": display_name
                    })
                
                # Get results for display
                select_sql = text(f"""
                    SELECT ID, post_title, post_status, post_date, post_name, 
                           post_modified, guid, post_author
                    FROM `{posts_table}` 
                    WHERE {where_clause} 
                    ORDER BY post_date DESC 
                    LIMIT 100
                """)
                result = connection.execute(select_sql, params)
                rows = result.fetchall()
                
                # Display results
                results_table = Table(
                    title=f"{icon} {display_name} Search Results (showing up to 100 rows)",
                    expand=True,  # Use full terminal width
                    show_lines=True
                )

                # Calculate optimal column widths
                console_width = console.size.width
                column_keys = list(result.keys())  # Convert keys to a list for indexing
                col_width = max(25, (console_width - (len(column_keys) * 3)) // len(column_keys))

                # Add columns
                for column_name in column_keys:
                    if column_name == 'post_content':
                        content_width = max(80, col_width * 2)  # Give more space to content
                        results_table.add_column(column_name, overflow="fold", width=content_width, max_width=content_width)
                    else:
                        results_table.add_column(column_name, overflow="fold", width=col_width, max_width=col_width)
                
                # Add rows
                for row in rows:
                    string_values = []
                    for i, value in enumerate(row):
                        if column_keys[i] == 'post_content' and value:
                            # Truncate post_content to 100 characters when displaying
                            truncated_value = str(value)[:100]
                            if len(str(value)) > 100:
                                truncated_value += "..."
                            string_values.append(truncated_value)
                        else:
                            string_values.append(str(value) if value is not None else "")
                    
                    results_table.add_row(*string_values)
                
                console.print(results_table)
                return None
                
        elif search_type.startswith("2. Search by"):  # Search by post meta data
            # Get meta key filter prefix from user
            meta_prefix = console.input("[bold blue]Enter prefix to filter meta keys (leave empty for all): [/bold blue]")
            
            # Get available meta keys from postmeta table with filter
            with get_engine().connect() as connection:
                if meta_prefix:
                    meta_keys_sql = text(f"""
                        SELECT DISTINCT meta_key FROM `{postmeta_table}` pm 
                        JOIN `{posts_table}` p ON pm.post_id = p.ID
                        WHERE p.post_type = :post_type
                        AND meta_key LIKE :prefix 
                        ORDER BY meta_key LIMIT 500
                    """)
                    meta_keys_result = connection.execute(meta_keys_sql, {"post_type": post_type, "prefix": f"{meta_prefix}%"})
                else:
                    meta_keys_sql = text(f"""
                        SELECT DISTINCT meta_key FROM `{postmeta_table}` pm
                        JOIN `{posts_table}` p ON pm.post_id = p.ID
                        WHERE p.post_type = :post_type
                        ORDER BY meta_key LIMIT 500
                    """)
                    meta_keys_result = connection.execute(meta_keys_sql, {"post_type": post_type})
                
                meta_keys = [row[0] for row in meta_keys_result]
            
            # Meta data search
            if not meta_keys:
                console.print(f"⚠️ No {display_name.lower()} meta keys found matching the prefix.", style="bold yellow")
                return None if export_mode else None
            
            console.print(f"✅ Found {len(meta_keys)} meta keys" + (f" starting with '{meta_prefix}'" if meta_prefix else ""), style="bold green")
                
            # If in export mode, ask which filtered meta keys to include in the export
            # if export_mode:
            #     meta_key_choices = [(meta_key, meta_key) for meta_key in meta_keys]
                
            #     console.print(f"Select which {display_name.lower()} meta keys to include in the export:", style="bold blue")
            #     meta_key_questions = [
            #         inquirer.Checkbox(
            #             "selected_meta_keys",
            #             message="Press space to select/deselect keys, Enter when done",
            #             choices=meta_key_choices,
            #         )
            #     ]
                
            #     meta_key_answers = inquirer.prompt(meta_key_questions)
            #     selected_export_meta_keys = meta_key_answers["selected_meta_keys"]
                
            #     if selected_export_meta_keys:
            #         console.print(f"✅ Will export {len(selected_export_meta_keys)} meta keys for each {display_name.lower()}", style="bold green")
                
            # Let user select a meta key for search
            meta_key_questions = [
                inquirer.List(
                    "meta_key",
                    message="Select a meta key to search by",
                    choices=meta_keys + ["Back"],
                )
            ]
            
            meta_key_answers = inquirer.prompt(meta_key_questions)
            selected_meta_key = meta_key_answers["meta_key"]
            
            if selected_meta_key == "Back":
                return None if export_mode else None
            
            # Show a sample value for the selected meta key
            with get_engine().connect() as connection:
                sample_sql = text(f"""
                    SELECT pm.post_id, pm.meta_value 
                    FROM `{postmeta_table}` pm
                    JOIN `{posts_table}` p ON pm.post_id = p.ID
                    WHERE p.post_type = :post_type
                    AND pm.meta_key = :meta_key
                    LIMIT 1
                """)
                
                sample_result = connection.execute(sample_sql, {"post_type": post_type, "meta_key": selected_meta_key})
                sample_row = sample_result.fetchone()
                
                if sample_row:
                    post_id, meta_value = sample_row
                    # Format the output based on the meta value type and length
                    if meta_value is None:
                        formatted_value = "NULL"
                    elif len(str(meta_value)) > 100:
                        formatted_value = f"{str(meta_value)[:100]}... (truncated)"
                    else:
                        formatted_value = str(meta_value)
                    
                    console.print(f"📝 Sample value for '{selected_meta_key}':", style="bold cyan")
                    console.print(f"{display_name} ID: {post_id}", style="cyan")
                    console.print(f"Value: {formatted_value}", style="cyan")
                    console.print("")  # Add a blank line for better readability
                
            # Get search term and match type
            match_type = _get_match_type(f"'{selected_meta_key}' value")
            if match_type == "Back":
                return None if export_mode else None
            
            search_term = console.input(f"[bold blue]🔍 Enter search term for {selected_meta_key}: [/bold blue]")
            
            # Build the WHERE clause based on match type
            if match_type == "Exact match":
                meta_where_clause = "pm.meta_value = :search_term"
                params = {"post_type": post_type, "meta_key": selected_meta_key, "search_term": search_term}
            elif match_type == "Contains":  # Contains
                meta_where_clause = "pm.meta_value LIKE :search_term"
                params = {"post_type": post_type, "meta_key": selected_meta_key, "search_term": f"%{search_term}%"}
            elif match_type == "In list (comma separated)":
                # Split by comma and remove whitespace
                values = [v.strip() for v in search_term.split(",")]
                if not values:
                    console.print("❌ No valid values provided.", style="bold red")
                    return None if export_mode else None
                
                # Build IN clause parameters
                in_clause_params = {"post_type": post_type, "meta_key": selected_meta_key}
                in_clause_list = []
                for i, val in enumerate(values):
                    param_name = f"term_{i}"
                    in_clause_params[param_name] = val
                    in_clause_list.append(f":{param_name}")
                
                meta_where_clause = f"pm.meta_value IN ({', '.join(in_clause_list)})"
                params = in_clause_params
                
            # Execute the meta search query
            with get_engine().connect() as connection:
                # Join posts and postmeta tables
                query = f"""
                    SELECT p.* 
                    FROM `{posts_table}` p
                    INNER JOIN `{postmeta_table}` pm ON p.ID = pm.post_id
                    WHERE p.post_type = :post_type
                    AND pm.meta_key = :meta_key
                    AND {meta_where_clause}
                """
                
                # If in export mode, return the query and params
                if export_mode:
                    count_sql = text(f"""
                        SELECT COUNT(DISTINCT p.ID) 
                        FROM `{posts_table}` p
                        INNER JOIN `{postmeta_table}` pm ON p.ID = pm.post_id
                        WHERE p.post_type = :post_type
                        AND pm.meta_key = :meta_key AND {meta_where_clause}
                    """)
                    count_result = connection.execute(count_sql, params)
                    count = count_result.scalar()
                    
                    if count == 0:
                        console.print(f"⚠️ No matching {display_name.lower()}s found.", style="bold yellow")
                        return None
                        
                    console.print(f"✅ Found {count} matching {display_name.lower()}s", style="bold green")
                    
                    
                    # First get all available meta keys for this post type
                    all_meta_keys_sql = text(f"""
                        SELECT DISTINCT meta_key FROM `{postmeta_table}` pm
                        JOIN `{posts_table}` p ON pm.post_id = p.ID
                        WHERE p.post_type = :post_type
                        ORDER BY meta_key 
                        LIMIT 500
                    """)
                    all_meta_keys_result = connection.execute(all_meta_keys_sql, {"post_type": post_type})
                    all_meta_keys = [row[0] for row in all_meta_keys_result]
                    
                    # Ask user to select which meta keys to include in export
                    if all_meta_keys:
                        meta_key_choices = [(meta_key, meta_key) for meta_key in all_meta_keys]
                        
                        console.print(f"Select which {display_name.lower()} meta keys to include in the export:", style="bold blue")
                        meta_key_questions = [
                            inquirer.Checkbox(
                                "selected_meta_keys",
                                message="Press space to select/deselect keys, Enter when done",
                                choices=meta_key_choices,
                            )
                        ]
                        
                        meta_key_answers = inquirer.prompt(meta_key_questions)
                        selected_export_meta_keys = meta_key_answers["selected_meta_keys"]
                        
                        if selected_export_meta_keys:
                            console.print(f"✅ Will export {len(selected_export_meta_keys)} meta keys for each {display_name.lower()}", style="bold green")
                                    
                    return (
                        query, 
                        params, 
                        {
                            "count": count, 
                            "table": posts_table, 
                            "meta_table": postmeta_table,
                            "meta_key": selected_meta_key,
                            "is_meta": True,
                            "export_meta_keys": selected_export_meta_keys,
                            "post_type": post_type,
                            "display_name": display_name
                        }
                    )
                
                # For regular search mode
                display_sql = text(f"""
                    SELECT p.ID, p.post_title, p.post_status, p.post_date, p.post_name,
                           p.post_modified, p.guid, p.post_author, p.post_content
                    FROM `{posts_table}` p
                    INNER JOIN `{postmeta_table}` pm ON p.ID = pm.post_id
                    WHERE p.post_type = :post_type
                    AND pm.meta_key = :meta_key
                    AND {meta_where_clause}
                    ORDER BY p.post_date DESC
                    LIMIT 100
                """)
                result = connection.execute(display_sql, params)
                rows = result.fetchall()
                count = len(rows)
                
                if count == 0:
                    console.print(f"⚠️ No matching {display_name.lower()}s found.", style="bold yellow")
                    return None
                
                console.print(f"✅ Found {count} matching {display_name.lower()}s", style="bold green")
                
                # Display results
                results_table = Table(
                    title=f"{icon} {display_name} Search Results (showing up to 100 rows)",
                    expand=True,  # Use full terminal width
                    show_lines=True
                )

                # Calculate optimal column widths
                console_width = console.size.width
                column_keys = list(result.keys())  # Convert keys to a list for indexing
                col_width = max(25, (console_width - (len(column_keys) * 3)) // len(column_keys))

                # Add columns
                for column_name in column_keys:
                    if column_name == 'post_content':
                        content_width = max(80, col_width * 2)  # Give more space to content
                        results_table.add_column(column_name, overflow="fold", width=content_width, max_width=content_width)
                    else:
                        results_table.add_column(column_name, overflow="fold", width=col_width, max_width=col_width)
                
                # Add rows
                for row in rows:
                    string_values = []
                    for i, value in enumerate(row):
                        if column_keys[i] == 'post_content' and value:
                            # Truncate post_content to 100 characters when displaying
                            truncated_value = str(value)[:100]
                            if len(str(value)) > 100:
                                truncated_value += "..."
                            string_values.append(truncated_value)
                        else:
                            string_values.append(str(value) if value is not None else "")
                    
                    results_table.add_row(*string_values)
                
                console.print(results_table)
                return None
                
    except Exception as e:
        console.print(f"❌ {display_name} search failed: {e}", style="bold red")
        return None if export_mode else None
        
def search_orders(export_mode=False):
    """Search WooCommerce orders - calls the generic search_posts function"""
    return search_posts(post_type="shop_order", export_mode=export_mode, display_name="Order")

def search_coupons(export_mode=False):
    """Search WooCommerce coupons - calls the generic search_posts function"""
    return search_posts(post_type="shop_coupon", export_mode=export_mode, display_name="Coupon")

def search_regular_posts(export_mode=False):
    """Search WordPress posts - calls the generic search_posts function"""
    return search_posts(post_type="post", export_mode=export_mode, display_name="Post")

def search_custom_post_type(export_mode=False):
    """Search a custom post type selected by the user"""
    custom_types = get_available_post_types()
    
    if not custom_types:
        console.print("⚠️ No custom post types found in the database.", style="bold yellow")
        return None if export_mode else None
    
    # Let the user select a post type
    type_questions = [
        inquirer.List(
            "post_type",
            message="Select custom post type to search",
            choices=custom_types + ["Back"],
        )
    ]
    
    type_answers = inquirer.prompt(type_questions)
    selected_type = type_answers["post_type"]
    
    if selected_type == "Back":
        return None if export_mode else None
    
    # Use the generic search_posts function with the selected post type
    return search_posts(post_type=selected_type, export_mode=export_mode)

def get_available_post_types():
    """
    Discover available post types in the WordPress database
    
    Returns:
    list: List of post types excluding the standard ones
    """
    # standard_types = ['post', 'page', 'attachment', 'revision', 'nav_menu_item', 
    #                  'custom_css', 'customize_changeset', 'shop_order', 'shop_coupon']
    standard_types = []
    
    try:
        with get_engine().connect() as connection:
            # Get distinct post types from posts table
            post_types_sql = text(f"""
                SELECT DISTINCT post_type 
                FROM `{posts_table}` 
                WHERE post_type NOT IN ('shop_order', 'shop_coupon', 'post', 'page',
                                       'attachment', 'revision', 'nav_menu_item', 
                                       'custom_css', 'customize_changeset')
                ORDER BY post_type
            """)
            result = connection.execute(post_types_sql)
            custom_types = [row[0] for row in result if row[0] not in standard_types]
            return custom_types
    except Exception as e:
        console.print(f"❌ Failed to get post types: {e}", style="bold red")
        return []

def general_search():
    """General search across all tables"""
    try:
        search_term = console.input("[bold blue]🔍 Enter search term: [/bold blue]")
        table_results = {}

        # Get all table names and filter by prefix
        available_tables = [name for name in get_inspector().get_table_names() if name.startswith(table_prefix)]
        
        # If no tables match the prefix, inform the user
        if not available_tables:
            console.print(f"⚠️ No tables found with prefix '{table_prefix}'", style="bold yellow")
            return
            
        console.print(f"🔍 Searching through {len(available_tables)} tables...", style="bold blue")
        
        # For each matching table, try to search and count results
        for table_name in available_tables:
            try:
                # Use raw SQL for the search with SQL LIKE for pattern matching
                with get_engine().connect() as connection:
                    # Get all column names for the table
                    columns_info = get_inspector().get_columns(table_name)
                    column_names = [col['name'] for col in columns_info]
                    
                    # Build a WHERE clause to search across all columns with OR conditions
                    where_conditions = []
                    for col in column_names:
                        where_conditions.append(f"`{col}` LIKE :search_term")
                    
                    # Skip if no columns (shouldn't happen)
                    if not where_conditions:
                        continue
                        
                    where_clause = " OR ".join(where_conditions)
                    
                    # Query to count matching rows
                    count_sql = text(f"SELECT COUNT(*) FROM `{table_name}` WHERE {where_clause}")
                    count_result = connection.execute(count_sql, {"search_term": f"%{search_term}%"})
                    count = count_result.scalar()
                    
                    if count > 0:
                        table_results[table_name] = count
            except Exception as e:
                console.print(f"⚠️ Error searching table {table_name}: {e}", style="yellow")
                continue

        # Display results
        if table_results:
            result_table = Table(
                title="🔍 Search Results",
                expand=True,  # Use full terminal width
                show_lines=True
            )
            result_table.add_column("Table Name", style="cyan", width=50)
            result_table.add_column("Matches", style="green", justify="center", width=20)
            
            for table_name, count in table_results.items():
                result_table.add_row(table_name, str(count))
                
            console.print(result_table)
            
            # Prompt user to select a table to view results
            view_results(engine, table_results, search_term)
        else:
            console.print("⚠️ No matching results found.", style="bold yellow")
    except Exception as e:
        console.print(f"❌ Search failed: {e}", style="bold red")

def view_results(engine, table_results, search_term):
    """Allow user to select and view search results for a specific table"""
    if not table_results:
        return
        
    # Add an option to go back
    choices = list(table_results.keys()) + ["Back"]
    
    questions = [
        inquirer.List(
            "selected_table",
            message="Select a table to view results",
            choices=choices,
        )
    ]
    
    answers = inquirer.prompt(questions)
    selected_table = answers["selected_table"]
    
    if selected_table == "Back":
        return
        
    try:
        # Get table schema to retrieve column names
        columns_info = get_inspector().get_columns(selected_table)
        column_names = [col['name'] for col in columns_info]
        
        # Build a WHERE clause to search across all columns with OR conditions
        where_conditions = []
        for col in column_names:
            where_conditions.append(f"`{col}` LIKE :search_term")
            
        where_clause = " OR ".join(where_conditions)
        
        # Query to get matching rows (limited to 100)
        with get_engine().connect() as connection:
            select_sql = text(f"SELECT * FROM `{selected_table}` WHERE {where_clause} LIMIT 100")
            result = connection.execute(select_sql, {"search_term": f"%{search_term}%"})
            
            # Get the results
            rows = result.fetchall()
            
            if not rows:
                console.print("⚠️ No rows found.", style="bold yellow")
                return
                
            # Create a table for displaying the results
            results_table = Table(
                title=f"🔍 Results from {selected_table} (showing up to 100 rows)",
                expand=True,  # Use full terminal width
                show_lines=True
            )

            # Calculate optimal column widths
            console_width = console.size.width
            column_keys = list(result.keys())
            col_width = max(20, (console_width - (len(column_keys) * 3)) // len(column_keys))

            # Add columns to the table
            for column_name in result.keys():
                results_table.add_column(column_name, overflow="fold", width=col_width, max_width=col_width)
                
            # Add rows to the table
            for row in rows:
                # Convert all values to strings
                string_values = [str(value) if value is not None else "" for value in row]
                results_table.add_row(*string_values)
                
            # Print the table with results
            console.print(results_table)
            
    except Exception as e:
        console.print(f"❌ Error viewing results: {e}", style="bold red")

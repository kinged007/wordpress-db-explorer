import os
import json
import csv
import datetime
from pathlib import Path
import inquirer
from rich.console import Console
from rich.progress import Progress
from sqlalchemy.sql import text
from dotenv import load_dotenv

from src.db_utils import get_db_engine, check_db_connection_with_friendly_error
from src.search_utils import search_users, search_orders, search_coupons, search_regular_posts, get_engine, table_prefix

console = Console()
load_dotenv(override=True)

# Set common export parameters
BATCH_SIZE = 1000
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)

def _get_csv_export_options():
    """Prompt user for CSV export options"""
    # First get the basic options
    basic_questions = [
        inquirer.List(
            "separator",
            message="📄 Select CSV separator",
            choices=[
                ("Comma (,)", ","),
                ("Semicolon (;)", ";"),
                ("Tab (\\t)", "\t"),
            ],
            default=","
        ),
        inquirer.List(
            "encoding",
            message="🔤 Select file encoding",
            choices=[
                ("UTF-8", "utf-8"),
                ("ISO-8859-1 (Latin-1)", "iso-8859-1"),
                ("Windows-1252", "windows-1252"),
            ],
            default="utf-8"
        ),
        inquirer.List(
            "headings",
            message="🏷️ Select heading base style",
            choices=[
                ("No change", "no_change"),
                ("Force Snake Case", "snake_case"),
                ("Force Title Case", "title_case"),
            ],
            default="no_change"
        ),
    ]
    
    console.print("\n📋 CSV Export Options:", style="bold blue")
    basic_answers = inquirer.prompt(basic_questions)
    
    if basic_answers is None:  # User pressed Ctrl+C
        return {
            "separator": ",",
            "encoding": "utf-8",
            "headings": "no_change",
            "ensure_valid_identifiers": False
        }
    
    # Now ask about additional heading options
    heading_questions = [
        inquirer.Confirm(
            "ensure_valid_identifiers",
            message="Ensure all headings are valid identifiers (prefix invalid ones with 'a_')?",
            default=False
        ),
    ]
    
    heading_answers = inquirer.prompt(heading_questions)
    
    if heading_answers is None:  # User pressed Ctrl+C
        heading_answers = {"ensure_valid_identifiers": False}
    
    # Combine the answers
    return {
        "separator": basic_answers["separator"],
        "encoding": basic_answers["encoding"],
        "headings": basic_answers["headings"],
        "ensure_valid_identifiers": heading_answers["ensure_valid_identifiers"]
    }

def _transform_header(header, style, ensure_valid_identifiers=False):
    """Transform header based on selected style and optionally ensure it's a valid identifier"""
    # First ensure it's a string
    header_str = str(header)
    
    # Apply the base style
    if style == "no_change":
        transformed = header_str
    elif style == "snake_case":
        # Convert to lowercase and replace spaces with underscores
        transformed = header_str.lower().replace(' ', '_').replace('-', '_')
    elif style == "title_case":
        # Capitalize first letter of each word
        transformed = ' '.join(word.capitalize() for word in header_str.split())
    elif style == "valid_identifier":  # Legacy support
        # This option is deprecated but kept for backward compatibility
        ensure_valid_identifiers = True
        transformed = header_str
    else:
        transformed = header_str
    
    # Then ensure it's a valid identifier if requested
    if ensure_valid_identifiers:
        # Ensure the header starts with a letter or underscore
        if not transformed or not (transformed[0].isalpha() or transformed[0] == '_'):
            transformed = 'a_' + transformed
        # Also replace any invalid characters with underscores
        import re
        transformed = re.sub(r'[^a-zA-Z0-9_]', '_', transformed)
    
    return transformed

def export_users():
    """Export users with filtering options using the search_users function"""
    try:
        # Use the search_users function in export mode to get the query and params
        search_result = search_users(export_mode=True)
        
        if search_result is None:
            return  # User cancelled or no results found
        
        query, params, meta_info = search_result
        count = meta_info["count"]
        export_meta_keys = meta_info.get("export_meta_keys", [])
        
        # Select export format
        format_questions = [
            inquirer.List(
                "export_format",
                message="📊 Select export format",
                choices=["JSON", "CSV", "Back"],
            )
        ]
        
        format_answers = inquirer.prompt(format_questions)
        export_format = format_answers["export_format"]
        
        if export_format == "Back":
            return
        
        # Get CSV export options if CSV format selected
        csv_options = None
        if export_format == "CSV":
            csv_options = _get_csv_export_options()
        
        # Set fixed batch size - now using the global constant
        batch_size = BATCH_SIZE
        console.print(f"Using batch size of {batch_size} records", style="bold green")
            
        # Create output file and prepare for batched export
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        exports_dir = EXPORTS_DIR
        
        if export_format == "JSON":
            filepath = exports_dir / f"users_{timestamp}.json"
            export_func = _export_batch_to_json
        else:  # CSV
            filepath = exports_dir / f"users_{timestamp}.csv"
            export_func = _export_batch_to_csv
            
        engine = get_db_engine()
        
        # If we need to export meta keys, prepare the query
        meta_table = meta_info.get("meta_table")
        users_table = meta_info["table"]
        
        # Initialize the export file
        if export_format == "CSV":
            # For CSV, we need to write the header first
            with get_engine().connect() as connection:
                # Get base column names 
                limit_query = f"{query} LIMIT 1"
                header_result = connection.execute(text(limit_query), params)
                base_columns = header_result.keys()
                
                # Create header with base columns + selected meta keys
                all_columns = list(base_columns) + export_meta_keys
                
                # Transform headers based on selected style
                if csv_options:
                    all_columns = [_transform_header(
                        col, 
                        csv_options["headings"],
                        csv_options.get("ensure_valid_identifiers", False)
                    ) for col in all_columns]
                
                with open(filepath, 'w', newline='', encoding=csv_options["encoding"] if csv_options else 'utf-8') as f:
                    writer = csv.writer(f, delimiter=csv_options["separator"] if csv_options else ',')
                    writer.writerow(all_columns)
        else:
            # For JSON, just create an empty file with array brackets
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("[\n")
                
        # Export in batches with progress tracking
        with Progress() as progress:
            task = progress.add_task("[green]Exporting users...", total=count)
            
            offset = 0
            records_exported = 0
            first_batch = True
            
            # Add pagination to the query
            paginated_query = f"{query} LIMIT :batch_size OFFSET :offset"
            
            while records_exported < count:
                with get_engine().connect() as connection:
                    # Execute query with pagination
                    batch_result = connection.execute(
                        text(paginated_query),
                        {**params, "batch_size": batch_size, "offset": offset}
                    )
                    
                    # Get batch data
                    rows = batch_result.fetchall()
                    if not rows:
                        break
                    
                    batch_size_actual = len(rows)
                    
                    # Convert to list of dicts for base data
                    column_names = batch_result.keys()
                    batch_data = [dict(zip(column_names, row)) for row in rows]
                    
                    # If we have meta keys to export, fetch them
                    if export_meta_keys:
                        user_ids = [row['ID'] for row in batch_data]
                        placeholders = ', '.join([':id' + str(i) for i in range(len(user_ids))])
                        meta_key_placeholders = ', '.join([':meta' + str(i) for i in range(len(export_meta_keys))])
                        
                        # Create a query to get all selected meta data for these users
                        meta_query = f"""
                            SELECT user_id, meta_key, meta_value 
                            FROM `{meta_table}` 
                            WHERE user_id IN ({placeholders})
                            AND meta_key IN ({meta_key_placeholders})
                        """
                        
                        # Prepare parameters for the meta query
                        meta_params = {}
                        for i, user_id in enumerate(user_ids):
                            meta_params[f'id{i}'] = user_id
                        
                        for i, meta_key in enumerate(export_meta_keys):
                            meta_params[f'meta{i}'] = meta_key
                            
                        # Execute meta query
                        meta_result = connection.execute(text(meta_query), meta_params)
                        meta_rows = meta_result.fetchall()
                        
                        # Organize meta data by user_id and meta_key
                        user_meta_data = {}
                        for meta_row in meta_rows:
                            user_id = meta_row[0]
                            meta_key = meta_row[1]
                            meta_value = meta_row[2]
                            
                            if user_id not in user_meta_data:
                                user_meta_data[user_id] = {}
                                
                            user_meta_data[user_id][meta_key] = meta_value
                        
                        # Add meta data to batch data
                        for record in batch_data:
                            user_id = record['ID']
                            if user_id in user_meta_data:
                                for meta_key in export_meta_keys:
                                    record[meta_key] = user_meta_data[user_id].get(meta_key, None)
                            else:
                                for meta_key in export_meta_keys:
                                    record[meta_key] = None
                    
                    # Export this batch
                    export_func(batch_data, filepath, first_batch, records_exported + batch_size_actual >= count, csv_options)
                    
                    # Update progress
                    progress.update(task, advance=batch_size_actual)
                    records_exported += batch_size_actual
                    offset += batch_size
                    first_batch = False
                    
        console.print(f"✅ Successfully exported {records_exported} users to {filepath}", style="bold green")
                
    except Exception as e:
        console.print(f"❌ User export failed: {e}", style="bold red")

def export_posts(post_type, display_name=None):
    """
    Generic function to export any WordPress post type
    
    Parameters:
    post_type (str): The post type to export (e.g. 'shop_order', 'shop_coupon', 'post')
    display_name (str): Display name for the post type (e.g. "Order", "Coupon", "Post")
    """
    if display_name is None:
        display_name = post_type.replace('_', ' ').title()
        
    try:
        # Use the appropriate search function in export mode
        if post_type == "shop_order":
            search_result = search_orders(export_mode=True)
        elif post_type == "shop_coupon":
            search_result = search_coupons(export_mode=True)
        elif post_type == "post":
            search_result = search_regular_posts(export_mode=True)
        else:
            # Generic search for any other post type
            from src.search_utils import search_posts
            search_result = search_posts(post_type=post_type, export_mode=True, display_name=display_name)
        
        if search_result is None:
            return  # User cancelled or no results found
        
        query, params, meta_info = search_result
        count = meta_info["count"]
        export_meta_keys = meta_info.get("export_meta_keys", [])
        
        # Select export format
        format_questions = [
            inquirer.List(
                "export_format",
                message="📊 Select export format",
                choices=["JSON", "CSV", "Back"],
            )
        ]
        
        format_answers = inquirer.prompt(format_questions)
        export_format = format_answers["export_format"]
        
        if export_format == "Back":
            return
        
        # Get CSV export options if CSV format selected
        csv_options = None
        if export_format == "CSV":
            csv_options = _get_csv_export_options()
        
        # Set fixed batch size
        batch_size = BATCH_SIZE
        console.print(f"Using batch size of {batch_size} records", style="bold green")
            
        # Create output file and prepare for batched export
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        exports_dir = EXPORTS_DIR
        
        if export_format == "JSON":
            filepath = exports_dir / f"{post_type}_{timestamp}.json"
            export_func = _export_batch_to_json
        else:  # CSV
            filepath = exports_dir / f"{post_type}_{timestamp}.csv"
            export_func = _export_batch_to_csv
        
        # If we need to export meta keys, prepare the query
        meta_table = meta_info.get("meta_table")
        posts_table = meta_info["table"]
        
        # Initialize the export file
        if export_format == "CSV":
            # For CSV, we need to write the header first
            with get_engine().connect() as connection:
                # Get base column names 
                limit_query = f"{query} LIMIT 1"
                header_result = connection.execute(text(limit_query), params)
                base_columns = header_result.keys()
                
                # Create header with base columns + selected meta keys
                all_columns = list(base_columns) + export_meta_keys
                
                # Transform headers based on selected style
                if csv_options:
                    all_columns = [_transform_header(
                        col, 
                        csv_options["headings"],
                        csv_options.get("ensure_valid_identifiers", False)
                    ) for col in all_columns]
                
                with open(filepath, 'w', newline='', encoding=csv_options["encoding"] if csv_options else 'utf-8') as f:
                    writer = csv.writer(f, delimiter=csv_options["separator"] if csv_options else ',')
                    writer.writerow(all_columns)
        else:
            # For JSON, just create an empty file with array brackets
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("[\n")
                
        # Export in batches with progress tracking
        with Progress() as progress:
            task = progress.add_task(f"[green]Exporting {display_name.lower()}s...", total=count)
            
            offset = 0
            records_exported = 0
            first_batch = True
            
            # Add pagination to the query
            paginated_query = f"{query} LIMIT :batch_size OFFSET :offset"
            
            while records_exported < count:
                with get_engine().connect() as connection:
                    # Execute query with pagination
                    batch_result = connection.execute(
                        text(paginated_query),
                        {**params, "batch_size": batch_size, "offset": offset}
                    )
                    
                    # Get batch data
                    rows = batch_result.fetchall()
                    if not rows:
                        break
                    
                    batch_size_actual = len(rows)
                    
                    # Convert to list of dicts for base data
                    column_names = batch_result.keys()
                    batch_data = [dict(zip(column_names, row)) for row in rows]
                    
                    # If we have meta keys to export, fetch them
                    if export_meta_keys:
                        post_ids = [row['ID'] for row in batch_data]
                        placeholders = ', '.join([':id' + str(i) for i in range(len(post_ids))])
                        meta_key_placeholders = ', '.join([':meta' + str(i) for i in range(len(export_meta_keys))])
                        
                        # Create a query to get all selected meta data for these posts
                        meta_query = f"""
                            SELECT post_id, meta_key, meta_value 
                            FROM `{meta_table}` 
                            WHERE post_id IN ({placeholders})
                            AND meta_key IN ({meta_key_placeholders})
                        """
                        
                        # Prepare parameters for the meta query
                        meta_params = {}
                        for i, post_id in enumerate(post_ids):
                            meta_params[f'id{i}'] = post_id
                        
                        for i, meta_key in enumerate(export_meta_keys):
                            meta_params[f'meta{i}'] = meta_key
                            
                        # Execute meta query
                        meta_result = connection.execute(text(meta_query), meta_params)
                        meta_rows = meta_result.fetchall()
                        
                        # Organize meta data by post_id and meta_key
                        post_meta_data = {}
                        for meta_row in meta_rows:
                            post_id = meta_row[0]
                            meta_key = meta_row[1]
                            meta_value = meta_row[2]
                            
                            if post_id not in post_meta_data:
                                post_meta_data[post_id] = {}
                                
                            post_meta_data[post_id][meta_key] = meta_value
                        
                        # Add meta data to batch data
                        for record in batch_data:
                            post_id = record['ID']
                            if post_id in post_meta_data:
                                for meta_key in export_meta_keys:
                                    record[meta_key] = post_meta_data[post_id].get(meta_key, None)
                            else:
                                for meta_key in export_meta_keys:
                                    record[meta_key] = None
                    
                    # Export this batch
                    export_func(batch_data, filepath, first_batch, records_exported + batch_size_actual >= count, csv_options)
                    
                    # Update progress
                    progress.update(task, advance=batch_size_actual)
                    records_exported += batch_size_actual
                    offset += batch_size
                    first_batch = False
                    
        console.print(f"✅ Successfully exported {records_exported} {display_name.lower()}s to {filepath}", style="bold green")
                
    except Exception as e:
        console.print(f"❌ {display_name} export failed: {e}", style="bold red")

def export_custom_post_type():
    """Export a custom post type selected by the user"""
    # Import here to avoid circular imports
    from src.search_utils import get_available_post_types
    
    custom_types = get_available_post_types()
    
    if not custom_types:
        console.print("⚠️ No custom post types found in the database.", style="bold yellow")
        return
    
    # Let the user select a post type
    type_questions = [
        inquirer.List(
            "post_type",
            message="Select custom post type to export",
            choices=custom_types + ["Back"],
        )
    ]
    
    type_answers = inquirer.prompt(type_questions)
    selected_type = type_answers["post_type"]
    
    if selected_type == "Back":
        return
    
    # Use the generic export_posts function with the selected post type
    export_posts(post_type=selected_type)

def _export_batch_to_json(data, filepath, is_first_batch, is_last_batch):
    """Export a batch of data to a JSON file with appropriate formatting"""
    try:
        # Process data for JSON serialization
        processed_data = []
        for item in data:
            processed_item = {}
            for key, value in item.items():
                if isinstance(value, datetime.datetime):
                    processed_item[key] = value.isoformat()
                elif isinstance(value, bytes):
                    processed_item[key] = value.decode('utf-8', errors='ignore')
                else:
                    processed_item[key] = value
            processed_data.append(processed_item)
        
        # Convert to JSON string
        json_str = json.dumps(processed_data, indent=2, ensure_ascii=False)
        
        # Remove the surrounding brackets from the JSON string
        json_content = json_str.strip()[1:-1].strip()
        
        with open(filepath, 'a', encoding='utf-8') as f:
            if not is_first_batch:
                f.write(",\n")
            f.write(json_content)
            
            if is_last_batch:
                f.write("\n]")
        
    except Exception as e:
        console.print(f"❌ JSON batch export failed: {e}", style="bold red")

def _export_batch_to_csv(data, filepath, is_first_batch, is_last_batch, csv_options=None):
    """Export a batch of data to a CSV file"""
    try:
        # Use default options if none provided
        if csv_options is None:
            csv_options = {
                "separator": ",",
                "encoding": "utf-8",
                "headings": "no_change"
            }
        
        with open(filepath, 'a', newline='', encoding=csv_options["encoding"]) as f:
            # Configure CSV writer with proper quoting for data with commas
            writer = csv.writer(
                f, 
                delimiter=csv_options["separator"],
                quoting=csv.QUOTE_MINIMAL,     # Quote fields only if needed (contains delimiter or quotes)
                quotechar='"',                 # Use double quotes as default
                escapechar=None,               # Let Python handle escaping automatically
                doublequote=True               # Escape quotes by doubling them (standard CSV behavior)
            )
            
            # Process and write each row
            for row_dict in data:
                processed_row = []
                for key, value in row_dict.items():
                    if isinstance(value, datetime.datetime):
                        processed_value = value.isoformat()
                    elif isinstance(value, bytes):
                        processed_value = value.decode('utf-8', errors='ignore')
                    else:
                        processed_value = value
                    processed_row.append(processed_value)
                writer.writerow(processed_row)
                
    except Exception as e:
        console.print(f"❌ CSV batch export failed: {e}", style="bold red")

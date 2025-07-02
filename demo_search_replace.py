#!/usr/bin/env python3
"""
Demo script for the Search and Replace functionality
This script demonstrates the key features of the search and replace tool
"""

import sys
import os
from rich.console import Console
from rich.table import Table

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search_replace import (
    _safe_replace_in_serialized_data,
    _is_php_serialized,
    _is_json_data,
    SearchReplaceSession
)

console = Console()

def demo_serialized_data_handling():
    """Demonstrate safe serialized data handling"""
    console.print("\n🔧 Serialized Data Handling Demo", style="bold blue")
    console.print("=" * 50)
    
    # Demo data examples
    examples = [
        {
            "type": "Regular String",
            "data": "Welcome to example.com - the best site!",
            "search": "example.com",
            "replace": "newdomain.com"
        },
        {
            "type": "PHP Serialized Array",
            "data": 'a:3:{s:9:"site_name";s:12:"My WordPress";s:8:"site_url";s:20:"https://example.com";s:5:"admin";s:13:"admin@example.com";}',
            "search": "example.com",
            "replace": "newdomain.com"
        },
        {
            "type": "JSON Data",
            "data": '{"config": {"host": "old-server.com", "backup": "backup.old-server.com"}, "urls": ["https://old-server.com"]}',
            "search": "old-server.com",
            "replace": "new-server.com"
        },
        {
            "type": "WordPress Option",
            "data": 's:25:"https://mywordpress.com/";',
            "search": "mywordpress.com",
            "replace": "mynewsite.com"
        }
    ]
    
    for example in examples:
        console.print(f"\n📋 {example['type']}", style="bold cyan")
        console.print(f"Original: {example['data'][:80]}{'...' if len(example['data']) > 80 else ''}", style="dim")
        console.print(f"Search: '{example['search']}' → Replace: '{example['replace']}'", style="yellow")
        
        # Detect data type
        is_php = _is_php_serialized(example['data'])
        is_json = _is_json_data(example['data'])
        
        if is_php:
            console.print("🔍 Detected: PHP Serialized Data", style="green")
        elif is_json:
            console.print("🔍 Detected: JSON Data", style="green")
        else:
            console.print("🔍 Detected: Regular String", style="green")
        
        # Perform replacement
        result = _safe_replace_in_serialized_data(
            example['data'], 
            example['search'], 
            example['replace']
        )
        
        console.print(f"Result: {result[:80]}{'...' if len(result) > 80 else ''}", style="bold green")

def demo_session_management():
    """Demonstrate session management"""
    console.print("\n📊 Session Management Demo", style="bold blue")
    console.print("=" * 50)
    
    # Create a session
    session = SearchReplaceSession()
    
    # Configure session
    session.search_term = "example.com"
    session.replace_term = "newdomain.com"
    session.selected_tables = ["wp_posts", "wp_options", "wp_postmeta"]
    
    console.print("✅ Session Created", style="green")
    console.print(f"  Search Term: '{session.search_term}'", style="dim")
    console.print(f"  Replace Term: '{session.replace_term}'", style="dim")
    console.print(f"  Selected Tables: {', '.join(session.selected_tables)}", style="dim")
    
    # Create backup file
    backup_file = session.create_backup_file()
    console.print(f"📁 Backup File Created: {backup_file.name}", style="green")
    
    # Simulate some changes
    session.changes_made = [
        {
            "table": "wp_posts",
            "row_id": 1,
            "column": "post_content",
            "original_value": "Visit https://example.com for more info",
            "new_value": "Visit https://newdomain.com for more info"
        },
        {
            "table": "wp_options",
            "row_id": 2,
            "column": "option_value",
            "original_value": "s:20:\"https://example.com\";",
            "new_value": "s:21:\"https://newdomain.com\";"
        }
    ]
    
    console.print(f"🔄 Simulated {len(session.changes_made)} changes", style="yellow")
    
    # Clean up demo backup file
    if backup_file.exists():
        backup_file.unlink()
        console.print("🗑️  Demo backup file cleaned up", style="dim")

def demo_safety_features():
    """Demonstrate safety features"""
    console.print("\n🛡️  Safety Features Demo", style="bold blue")
    console.print("=" * 50)
    
    safety_table = Table(title="Safety Features")
    safety_table.add_column("Feature", style="cyan")
    safety_table.add_column("Description", style="white")
    safety_table.add_column("Benefit", style="green")
    
    safety_features = [
        ("Dry Run Mode", "Test replacements without making changes", "Preview results safely"),
        ("Backup Creation", "Automatic backup before any changes", "Complete undo capability"),
        ("Serialized Data Detection", "Automatically detect and handle serialized data", "Prevents data corruption"),
        ("Length Correction", "Fix string lengths in PHP serialized data", "Maintains data integrity"),
        ("Granular Selection", "Choose specific tables and rows", "Precise control"),
        ("Multiple Confirmations", "Several confirmation steps", "Prevents accidental changes"),
        ("Transaction Safety", "Database transactions with rollback", "Atomic operations"),
        ("Error Handling", "Graceful error handling and recovery", "Robust operation")
    ]
    
    for feature, description, benefit in safety_features:
        safety_table.add_row(feature, description, benefit)
    
    console.print(safety_table)

def demo_use_cases():
    """Demonstrate common use cases"""
    console.print("\n💡 Common Use Cases", style="bold blue")
    console.print("=" * 50)
    
    use_cases = [
        {
            "title": "Domain Migration",
            "description": "Change all references from old domain to new domain",
            "example": "old-site.com → new-site.com"
        },
        {
            "title": "URL Protocol Change",
            "description": "Update HTTP URLs to HTTPS",
            "example": "http:// → https://"
        },
        {
            "title": "Email Address Updates",
            "description": "Update admin email addresses across the site",
            "example": "admin@oldcompany.com → admin@newcompany.com"
        },
        {
            "title": "Content Updates",
            "description": "Replace outdated information in posts and pages",
            "example": "Old Product Name → New Product Name"
        },
        {
            "title": "Path Corrections",
            "description": "Fix file paths after server migration",
            "example": "/old/path/ → /new/path/"
        },
        {
            "title": "Branding Changes",
            "description": "Update company names and branding",
            "example": "Old Company LLC → New Company Inc"
        }
    ]
    
    for i, use_case in enumerate(use_cases, 1):
        console.print(f"\n{i}. {use_case['title']}", style="bold cyan")
        console.print(f"   {use_case['description']}", style="dim")
        console.print(f"   Example: {use_case['example']}", style="yellow")

def main():
    """Run the demo"""
    console.print("🚀 WordPress Database Search & Replace Tool Demo", style="bold magenta")
    console.print("This demo showcases the key features and capabilities", style="dim")
    
    try:
        demo_serialized_data_handling()
        demo_session_management()
        demo_safety_features()
        demo_use_cases()
        
        console.print("\n✅ Demo completed successfully!", style="bold green")
        console.print("\nTo use the search and replace tool:", style="bold")
        console.print("1. Run: python main.py", style="dim")
        console.print("2. Select '3. Search & Replace'", style="dim")
        console.print("3. Follow the interactive prompts", style="dim")
        console.print("\n⚠️  Always test with dry run first!", style="bold yellow")
        
    except Exception as e:
        console.print(f"❌ Demo error: {e}", style="bold red")

if __name__ == "__main__":
    main()

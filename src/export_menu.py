import inquirer
from rich.console import Console
from src.export_utils import (
    export_users, export_custom_post_type, export_posts
)

console = Console()

def export_menu():
    questions = [
        inquirer.List(
            "export_option",
            message="📤 Select data to export",
            choices=[
                "Users", 
                "WooCommerce Orders", 
                "WooCommerce Coupons", 
                "WordPress Posts", 
                "WordPress Pages", 
                "Custom Post Type",
                "Back"
            ],
        )
    ]
    answers = inquirer.prompt(questions)

    if answers["export_option"] == "Users":
        export_users()
    elif answers["export_option"] == "WooCommerce Orders":
        export_posts(post_type="shop_order", display_name="Order")
    elif answers["export_option"] == "WooCommerce Coupons":
        export_posts(post_type="shop_coupon", display_name="Coupon")
    elif answers["export_option"] == "WordPress Posts":
        export_posts(post_type="post", display_name="Post")
    elif answers["export_option"] == "WordPress Pages":
        export_posts(post_type="page", display_name="Page")
    elif answers["export_option"] == "Custom Post Type":
        export_custom_post_type()
    elif answers["export_option"] == "Back":
        return

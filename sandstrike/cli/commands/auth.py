"""
SandStrike API key management commands.

This module provides CLI commands for managing API keys and verifying
user subscriptions with the SandStrike platform.
"""

import os
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from sandstrike.sandstrike_auth import get_sandstrike_auth, UserSubscription, load_env_file
from sandstrike.exceptions import AvenlisError

console = Console()

# Load .env file when module is imported
load_env_file()


@click.group(name="auth")
def auth_group() -> None:
    """Manage SandStrike authentication and API keys."""
    pass


@auth_group.command(name="verify")
def verify_api_key() -> None:
    """Verify an API key and check subscription status."""
    try:
        # Get API key from environment
        api_key = os.getenv('AVENLIS_API_KEY')
        if not api_key:
            console.print("[red]No API key found[/red]")
            console.print("[yellow]Please set AVENLIS_API_KEY environment variable[/yellow]")
            console.print("[blue]Example:[/blue] export AVENLIS_API_KEY='your_api_key_here'")
            return
        
        api_key = api_key.strip()
        
        console.print("[blue]Verifying API key...[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Clearing cache and verifying with SandStrike Platform...", total=None)
            
            auth = get_sandstrike_auth()
            # Clear cache before verification
            auth.clear_stored_credentials()
            is_valid, subscription = auth.verify_api_key(api_key)
            
            if is_valid and subscription:
                progress.update(task, description="[SUCCESS] API key verified successfully")
                
                # Display user information
                user_panel = f"[bold]{subscription.first_name} {subscription.last_name}[/bold]\n"
                user_panel += f"[blue]Email:[/blue] {subscription.email}\n"
                
                # Handle subscription plan as string: "free", "plus", "pro"
                subscription_plan = subscription.subscription_plan
                if subscription_plan in ["plus", "pro"]:
                    user_panel += f"[blue]Subscription Plan:[/blue] SandStrike {subscription_plan.title()}\n"
                else:
                    user_panel += f"[blue]Subscription Plan:[/blue] SandStrike Free\n"
                
                if subscription.subscription_expires:
                    user_panel += f"\n[blue]Expires:[/blue] {subscription.subscription_expires.strftime('%Y-%m-%d %H:%M:%S')}"
                
                console.print(Panel(user_panel, title="User Information", border_style="green"))
                
                # Show subscription status with appropriate messaging
                if subscription_plan in ["plus", "pro"]:
                    console.print("\n[green]You have access to all SandStrike premium features![/green]")
                    if subscription_plan == "pro":
                        console.print("[blue]Pro plan includes advanced features and priority support.[/blue]")
                    else:
                        console.print("[blue]Plus plan includes unlimited prompts and premium features.[/blue]")
                else:
                    console.print("\n[yellow]WARNING: You have a free account. Upgrade to access premium features in SandStrike.[/yellow]")
                    console.print("[blue]Upgrade your account at:[/blue] https://avenlis.staterasolv.com/payment")
                    console.print("[dim]Premium features include: unlimited prompts, advanced encoding methods, detailed reports, and more.[/dim]")
                
            else:
                progress.update(task, description="[FAILED] API key verification failed")
                console.print("\n[red]Invalid API key or verification failed[/red]")
                console.print("[yellow]This could mean:[/yellow]")
                console.print("  • The API key doesn't exist")
                console.print("  • The API key has been deleted")
                console.print("  • The API key is inactive")
                console.print("  • Network connection issues")
                console.print("\n[blue]To get an API key:[/blue]")
                console.print("  1. Go to your SandStrike platform settings")
                console.print("  2. Navigate to the 'API Keys' section")
                console.print("  3. Create a new API key for SandStrike")
                console.print("  4. Copy the key and set it as AVENLIS_API_KEY environment variable")
                
    except Exception as e:
        console.print(f"[red]Error verifying API key:[/red] {e}")
        raise click.Abort()

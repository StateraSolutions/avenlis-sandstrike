"""
Dynamic Variables CLI Commands
"""
import click
import yaml
import os
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from sandstrike.storage import storage

console = Console()

@click.group(name="variables")
def variables_group():
    """Manage dynamic variables for prompt templates."""
    pass

@variables_group.command(name="set")
@click.option("--category", "-c", required=True, help="Variable category (e.g., application, data, system)")
@click.option("--name", "-n", required=True, help="Variable name")
@click.option("--value", "-v", required=True, help="Variable value")
@click.option("--source", "-s", type=click.Choice(['local', 'file']), help="Storage source (required): local (SQLite database) or file (YAML)")
def set_variable(category: str, name: str, value: str, source: str) -> None:
    """Set a dynamic variable value."""
    try:
        storage_instance = storage
        
        # Prompt for source if not provided
        if not source:
            source = Prompt.ask(
                "[yellow]Storage source (required):[/yellow]",
                choices=['local', 'file'],
                default='local'
            )
        
        # Normalize source to lowercase
        source = source.lower()
        
        # Validate input
        if len(value) > 100:
            console.print("[red]Error: Variable value too long (max 100 characters)[/red]")
            return
        
        # Set the variable
        success = storage_instance.set_dynamic_variable(category, name, value, source=source)
        
        if success:
            if source == 'file':
                console.print(f"[green][SUCCESS] Variable {category}.{name} set to '{value}' in dynamic_variables.yaml[/green]")
            else:
                console.print(f"[green][SUCCESS] Variable {category}.{name} set to '{value}' in {source} storage[/green]")
        else:
            console.print(f"[red][FAILED] Failed to set variable {category}.{name}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error setting variable: {e}[/red]")

@variables_group.command(name="list")
@click.option("--category", "-c", help="Variable category (optional: if not provided, shows all variables from all categories)")
@click.option("--source", type=click.Choice(['local', 'file', 'all']), default='all', help="Storage source filter")
def list_variables(category: Optional[str], source: str) -> None:
    """List dynamic variables. Shows all variables if category is not specified, or variables from a specific category."""
    try:
        storage_instance = storage
        
        if source == 'all':
            # Get from both sources
            local_vars = storage_instance.get_dynamic_variables(source='local')
            file_vars = storage_instance.get_dynamic_variables(source='file')
            
            # Merge variables (local takes precedence) and track sources
            merged_vars = {}
            var_sources = {}
            
            # First add file variables
            if file_vars and 'variables' in file_vars:
                merged_vars = file_vars['variables'].copy()
                for cat, vars_dict in file_vars['variables'].items():
                    if cat not in var_sources:
                        var_sources[cat] = {}
                    for var_name in vars_dict.keys():
                        var_sources[cat][var_name] = 'file'
            
            # Then add local variables (overwrites file variables)
            if local_vars and 'variables' in local_vars:
                for cat, vars_dict in local_vars['variables'].items():
                    if cat not in merged_vars:
                        merged_vars[cat] = {}
                    if cat not in var_sources:
                        var_sources[cat] = {}
                    for var_name, var_value in vars_dict.items():
                        merged_vars[cat][var_name] = var_value
                        var_sources[cat][var_name] = 'local'
            
            if category:
                # Show specific category
                if category in merged_vars:
                    console.print(f"[blue]Variables in category '{category}':[/blue]")
                    
                    # Create table with source column
                    table = Table(show_header=True, header_style="bold blue")
                    table.add_column("Variable", style="cyan", no_wrap=True)
                    table.add_column("Value", style="green")
                    table.add_column("Source", style="yellow", no_wrap=True)
                    
                    for var_name, var_value in merged_vars[category].items():
                        var_source = var_sources.get(category, {}).get(var_name, 'unknown')
                        table.add_row(var_name, str(var_value), var_source)
                    
                    console.print(table)
                else:
                    console.print(f"[yellow]Category '{category}' not found in any storage[/yellow]")
            else:
                # Show all categories and variables
                if not merged_vars:
                    console.print("[yellow]No variables found in any storage[/yellow]")
                    return
                
                console.print("[blue]Dynamic Variables[/blue]")
                
                # Prepare local variables dict first to check for overwrites
                local_only_vars = {}
                if local_vars and 'variables' in local_vars:
                    for cat, vars_dict in local_vars['variables'].items():
                        if cat not in local_only_vars:
                            local_only_vars[cat] = {}
                        for var_name, var_value in vars_dict.items():
                            local_only_vars[cat][var_name] = var_value
                
                # Show file variables first (only those not overwritten by local)
                file_only_vars = {}
                if file_vars and 'variables' in file_vars:
                    for cat, vars_dict in file_vars['variables'].items():
                        # Only show if not overwritten by local
                        if cat not in local_only_vars:
                            if cat not in file_only_vars:
                                file_only_vars[cat] = {}
                            for var_name, var_value in vars_dict.items():
                                file_only_vars[cat][var_name] = var_value
                
                if file_only_vars:
                    console.print("\n[blue]📁 File Storage Variables:[/blue]")
                    table = Table(title="File Variables")
                    table.add_column("Category", style="cyan")
                    table.add_column("Variable", style="white")
                    table.add_column("Value", style="green")
                    
                    for cat, vars_dict in file_only_vars.items():
                        for var_name, var_value in vars_dict.items():
                            display_value = str(var_value)[:50] + "..." if len(str(var_value)) > 50 else str(var_value)
                            table.add_row(cat, var_name, display_value)
                    
                    console.print(table)
                
                # Show local variables after file ones
                if local_only_vars:
                    console.print("\n[green]💾 Local Storage Variables:[/green]")
                    table = Table(title="Local Variables")
                    table.add_column("Category", style="cyan")
                    table.add_column("Variable", style="white")
                    table.add_column("Value", style="green")
                    
                    for cat, vars_dict in local_only_vars.items():
                        for var_name, var_value in vars_dict.items():
                            display_value = str(var_value)[:50] + "..." if len(str(var_value)) > 50 else str(var_value)
                            table.add_row(cat, var_name, display_value)
                    
                    console.print(table)
        else:
            # Single source
            variables = storage_instance.get_dynamic_variables(source=source)
            
            if not variables or 'variables' not in variables or not variables['variables']:
                console.print(f"[yellow]No variables found in {source} storage[/yellow]")
                return
            
            if category:
                # Show specific category
                if category in variables['variables']:
                    console.print(f"[blue]Variables in category '{category}' ({source} storage):[/blue]")
                    
                    # Create table with source column
                    table = Table(show_header=True, header_style="bold blue")
                    table.add_column("Variable", style="cyan", no_wrap=True)
                    table.add_column("Value", style="green")
                    table.add_column("Source", style="yellow", no_wrap=True)
                    
                    for var_name, var_value in variables['variables'][category].items():
                        table.add_row(var_name, str(var_value), source)
                    
                    console.print(table)
                else:
                    console.print(f"[yellow]Category '{category}' not found in {source} storage[/yellow]")
            else:
                # Show all categories
                console.print(f"[blue]Dynamic Variables ({source} storage)[/blue]")
                table = Table(title=f"{source.title()} Variables")
                table.add_column("Category", style="cyan")
                table.add_column("Variable", style="white")
                table.add_column("Value", style="green")
                
                for cat, vars_dict in variables['variables'].items():
                    for var_name, var_value in vars_dict.items():
                        display_value = str(var_value)[:50] + "..." if len(str(var_value)) > 50 else str(var_value)
                        table.add_row(cat, var_name, display_value)
                
                console.print(table)
                
    except Exception as e:
        console.print(f"[red]Error getting variables: {e}[/red]")
                
@variables_group.command(name="update")
@click.option("--category", "-c", required=True, help="Variable category")
@click.option("--name", "-n", required=True, help="Variable name")
@click.option("--value", "-v", required=True, help="New value for the variable")
@click.option("--source", "-s", type=click.Choice(['local', 'file']), help="Storage source (required): local (SQLite database) or file (YAML)")
def update_variable(category: str, name: str, value: str, source: str) -> None:
    """Update an existing dynamic variable."""
    try:
        storage_instance = storage
        
        # Prompt for source if not provided
        if not source:
            source = Prompt.ask(
                "[yellow]Storage source (required):[/yellow]",
                choices=['local', 'file'],
                default='local'
            )
        
        # Normalize source to lowercase
        source = source.lower()
        
        # Check if variable exists
        existing_value = storage_instance.get_dynamic_variable(category, name, source=source)
        if existing_value is None:
            console.print(f"[red][FAILED] Variable {category}.{name} not found in {source} storage[/red]")
            console.print(f"[yellow]Use 'sandstrike variables set' to create new variables[/yellow]")
            return
        
        # Update the variable
        success = storage_instance.set_dynamic_variable(category, name, value, source=source, overwrite=True)
        
        if success:
            if source == 'file':
                console.print(f"[green][SUCCESS] Variable {category}.{name} updated in dynamic_variables.yaml[/green]")
            else:
                console.print(f"[green][SUCCESS] Variable {category}.{name} updated in {source} storage[/green]")
            console.print(f"[blue]Old value: {existing_value}[/blue]")
            console.print(f"[blue]New value: {value}[/blue]")
        else:
            console.print(f"[red][FAILED] Failed to update variable {category}.{name}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error updating variable: {e}[/red]")







"""
Target management commands for the SandStrike CLI.

This module implements target management for organizing
scan targets (IP addresses/endpoints) for reuse in scans.
"""

from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from datetime import datetime

from sandstrike.config import AvenlisConfig
from sandstrike.main_storage import AvenlisStorage
from sandstrike.exceptions import AvenlisError

console = Console()


@click.group(name="targets")
def targets_group() -> None:
    """Manage scan targets for organized testing."""
    pass


@targets_group.command(name="create")
@click.option("--id", "target_id", required=True, help="Unique target ID (required)")
@click.option("--name", "-n", required=True, help="Target name (required)")
@click.option("--ip", "-i", required=True, help="IP address or URL (required, may include port)")
@click.option("--description", "-d", help="Description of the target (optional)")
@click.option("--target-type", "--type", "target_type", help="Target type (e.g., 'Ollama', 'URL'). Optional, defaults to 'URL'")
@click.option("--model", "-m", help="Model name (only used if target-type is 'Ollama'). Optional")
@click.option("--source", "-s", type=click.Choice(['file', 'local'], case_sensitive=False), required=True, help="Storage source (required): file (YAML) or local (SQLite database)")
def create_target(target_id: str, name: str, ip: str, description: Optional[str], target_type: Optional[str], model: Optional[str], source: str) -> None:
    """Create a new scan target."""
    
    try:
        # Validate model is only provided for Ollama targets
        if model and target_type and target_type.lower() != 'ollama':
            console.print(f"[yellow]Warning: Model parameter is only used for Ollama targets. Ignoring model '{model}' for target type '{target_type}'[/yellow]")
            model = None
        
        # If model is provided but target_type is not Ollama, warn user
        if model and (not target_type or target_type.lower() != 'ollama'):
            console.print(f"[yellow]Warning: Model parameter should only be used with target-type 'Ollama'. Setting target-type to 'Ollama'[/yellow]")
            target_type = 'Ollama'
        
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Normalize source to lowercase
        source = source.lower()
        
        if source == 'file':
            # Save to YAML file
            result_id = storage.create_yaml_target(
                target_id=target_id,
                name=name,
                ip_address=ip,
                description=description,
                target_type=target_type,
                model=model
            )
            
            if result_id:
                console.print(f"[green][SUCCESS] Created target:[/green] {name}")
                console.print(f"[blue]Target ID:[/blue] {target_id}")
                console.print(f"[blue]IP Address:[/blue] {ip}")
                console.print(f"[blue]Source:[/blue] YAML file")
                if target_type:
                    console.print(f"[blue]Target Type:[/blue] {target_type}")
                if model:
                    console.print(f"[blue]Model:[/blue] {model}")
                if description:
                    console.print(f"[blue]Description:[/blue] {description}")
        else:
            # Store in local database
            result_id = storage.create_target(
                target_id=target_id,
                name=name,
                ip_address=ip,
                description=description,
                target_type=target_type,
                model=model
            )
            if result_id:
                console.print(f"[green][SUCCESS] Created target:[/green] {name}")
                console.print(f"[blue]Target ID:[/blue] {target_id}")
                console.print(f"[blue]IP Address:[/blue] {ip}")
                console.print(f"[blue]Source:[/blue] local SQLite database")
                if target_type:
                    console.print(f"[blue]Target Type:[/blue] {target_type}")
                if model:
                    console.print(f"[blue]Model:[/blue] {model}")
                if description:
                    console.print(f"[blue]Description:[/blue] {description}")
        
    except AvenlisError as e:
        console.print(f"[red]Error creating target:[/red] {e}")
        raise click.Abort()


@targets_group.command(name="list")
@click.option("--source", type=click.Choice(['file', 'local'], case_sensitive=False), help="Filter by source: file (YAML) or local (database). Default: show all")
def list_targets(source: Optional[str]) -> None:
    """List all scan targets."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Get targets from both sources
        try:
            targets = storage.get_combined_targets()
        except Exception as e:
            console.print(f"[yellow]Warning: Error loading targets: {e}[/yellow]")
            targets = []
        
        # Ensure all targets have a source field set
        for target in targets:
            if 'source' not in target or not target.get('source'):
                # Default to 'local' if source is missing
                target['source'] = 'local'
        
        # Debug output to help diagnose
        if not targets:
            console.print("[dim]Debug: No targets found from get_combined_targets()[/dim]")
            # Try to get targets directly to see what's happening
            try:
                from .storage.yaml_loader import YAMLLoader
                yaml_loader = YAMLLoader()
                yaml_targets = yaml_loader.load_targets()
                console.print(f"[dim]Debug: Found {len(yaml_targets)} targets from YAML[/dim]")
            except Exception as e:
                console.print(f"[dim]Debug: Error loading YAML targets: {e}[/dim]")
            
            try:
                local_targets = storage.get_all_targets()
                console.print(f"[dim]Debug: Found {len(local_targets)} targets from local database[/dim]")
            except Exception as e:
                console.print(f"[dim]Debug: Error loading local targets: {e}[/dim]")
        
        # Filter by source if specified
        if source:
            source_lower = source.lower().strip()
            filtered_targets = []
            for target in targets:
                target_source = target.get('source', 'local')
                # Normalize target_source to lowercase for comparison
                target_source_lower = str(target_source).lower().strip() if target_source else 'local'
                if target_source_lower == source_lower:
                    filtered_targets.append(target)
            targets = filtered_targets
        
        if not targets:
            console.print("[yellow]No targets found[/yellow]")
            if source:
                console.print("[dim]Try adjusting your filter criteria[/dim]")
            else:
                console.print("[dim]Create your first target with:[/dim] [cyan]sandstrike targets create[/cyan]")
            return
        
        # Create table
        table = Table(title="Scan Targets")
        table.add_column("ID", style="cyan", no_wrap=True, width=20)
        table.add_column("Name", style="magenta", width=25)
        table.add_column("IP Address", style="white", width=30)
        table.add_column("Type", style="yellow", width=10)
        table.add_column("Model", style="green", width=15)
        table.add_column("Source", style="blue", width=12)
        table.add_column("Description", style="dim", width=25)
        
        for target in targets:
            # Truncate long descriptions
            desc = target.get('description', '') or ''
            if len(desc) > 22:
                desc = desc[:19] + "..."
            
            # Determine source type
            source_type = target.get('source', 'unknown')
            if source_type == 'file':
                source_display = "File"
            elif source_type == 'local':
                source_display = "Local"
            else:
                source_display = "Unknown"
            
            # Get target_type and model
            target_type = target.get('target_type', '')
            model = target.get('model', '')
            
            table.add_row(
                str(target['id']),
                target['name'],
                target['ip_address'],
                target_type or 'N/A',
                model or 'N/A',
                source_display,
                desc
            )
        
        console.print(table)
        console.print(f"\n[blue]Total:[/blue] {len(targets)} targets")
        
    except AvenlisError as e:
        console.print(f"[red]Error listing targets:[/red] {e}")
        raise click.Abort()


@targets_group.command(name="delete")
@click.option("--target-ids", "-t", help="Comma-separated list of target IDs to delete (e.g., 'target1,target2,target3')")
@click.option("--source", "-s", type=click.Choice(['file', 'local'], case_sensitive=False), help="Source filter: file (YAML) or local (SQLite database). If specified without target IDs, deletes all targets from that source")
def delete_target(target_ids: Optional[str], source: Optional[str]) -> None:
    """Delete scan target(s).
    
    Usage examples:
    - Delete specific targets: --target-ids target1,target2
    - Delete all targets from a source: --source file
    - Delete all targets from both sources: (no options)
    """
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Normalize source to lowercase if provided
        if source:
            source = source.lower()
        
        # Get all targets to determine what to delete
        all_targets = storage.get_combined_targets()
        
        # Determine which targets to delete
        targets_to_delete = []
        
        if target_ids:
            # Specific target IDs provided
            target_id_list = [tid.strip() for tid in target_ids.split(',')]
            
            for target_id in target_id_list:
                target = storage.get_target(target_id)
                if not target:
                    console.print(f"[yellow]Warning: Target '{target_id}' not found, skipping[/yellow]")
                    continue
                
                # Filter by source if specified
                if source and target.get('source') != source:
                    console.print(f"[yellow]Warning: Target '{target_id}' is not from source '{source}', skipping[/yellow]")
                    continue
                
                targets_to_delete.append(target)
        else:
            # No target IDs specified - delete all (optionally filtered by source)
            if source:
                # Delete all from specified source
                targets_to_delete = [t for t in all_targets if t.get('source') == source]
            else:
                # Delete all from both sources
                targets_to_delete = all_targets
        
        if not targets_to_delete:
            if target_ids:
                console.print("[yellow]No matching targets found to delete[/yellow]")
            elif source:
                console.print(f"[yellow]No targets found in source '{source}'[/yellow]")
            else:
                console.print("[yellow]No targets found to delete[/yellow]")
            return
        
        # Show deletion summary
        if len(targets_to_delete) == 1:
            target = targets_to_delete[0]
            console.print(f"[yellow]About to delete target:[/yellow] {target.get('name')}")
            console.print(f"[yellow]Target ID:[/yellow] {target.get('id')}")
            console.print(f"[yellow]IP Address:[/yellow] {target.get('ip_address', 'N/A')}")
            console.print(f"[yellow]Source:[/yellow] {target.get('source', 'unknown')}")
        else:
            console.print(f"[yellow]About to delete {len(targets_to_delete)} target(s):[/yellow]")
            for target in targets_to_delete:
                console.print(f"  - {target.get('name')} ({target.get('id')}) [{target.get('source', 'unknown')}]")
        
        # Confirm deletion
        if not Confirm.ask(f"[red]Are you sure you want to delete {len(targets_to_delete)} target(s)?[/red]"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return
        
        # Delete targets
        deleted_count = 0
        failed_count = 0
        
        for target in targets_to_delete:
            target_id = target.get('id')
            target_name = target.get('name', target_id)
            target_source = target.get('source', 'local')
            
            try:
                success = False
                if target_source == 'file':
                    success = storage.delete_yaml_target(target_id)
                else:
                    success = storage.delete_target(target_id)
                
                if success:
                    deleted_count += 1
                    console.print(f"[green]Deleted:[/green] {target_name} ({target_id})")
                else:
                    failed_count += 1
                    console.print(f"[red]Failed to delete:[/red] {target_name} ({target_id})")
            except Exception as e:
                failed_count += 1
                console.print(f"[red]Error deleting {target_name} ({target_id}):[/red] {e}")
        
        # Summary
        if deleted_count > 0:
            console.print(f"\n[green][SUCCESS] Deleted {deleted_count} target(s)[/green]")
        if failed_count > 0:
            console.print(f"[red]Failed to delete {failed_count} target(s)[/red]")
        
    except AvenlisError as e:
        console.print(f"[red]Error deleting target(s):[/red] {e}")
        raise click.Abort()


@targets_group.command(name="view")
@click.option("--target-ids", "-t", required=True, help="Comma-separated list of target IDs to view (required, e.g., 'target1,target2,target3')")
@click.option("--source", "-s", type=click.Choice(['file', 'local'], case_sensitive=False), required=True, help="Source filter (required): file (YAML) or local (SQLite database)")
def view_target(target_ids: str, source: str) -> None:
    """View detailed information about target(s).
    
    Required fields:
    - --target-ids: Comma-separated list of target IDs (e.g., 'target1,target2')
    - --source: Source type - 'file' for YAML targets or 'local' for database targets
    
    Examples:
    - View targets from file: --target-ids target1,target2 --source file
    - View targets from local: --target-ids target1 --source local
    """
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Normalize source to lowercase
        source = source.lower()
        
        # Parse target IDs
        target_id_list = [tid.strip() for tid in target_ids.split(',')]
        
        # Get all targets to find matches
        all_targets = storage.get_combined_targets()
        
        # Find targets to view
        targets_to_view = []
        for target_id in target_id_list:
            target = storage.get_target(target_id)
            if not target:
                console.print(f"[yellow]Warning: Target '{target_id}' not found, skipping[/yellow]")
                continue
            
            # Filter by source
            if target.get('source') != source:
                console.print(f"[yellow]Warning: Target '{target_id}' is not from source '{source}', skipping[/yellow]")
                continue
            
            targets_to_view.append(target)
        
        if not targets_to_view:
            console.print("[yellow]No matching targets found to view[/yellow]")
            if source:
                console.print(f"[dim]Try adjusting your filter criteria or check if targets exist in source '{source}'[/dim]")
            return
        
        # Display each target
        for i, target in enumerate(targets_to_view, 1):
            if len(targets_to_view) > 1:
                console.print(f"\n[bold blue]Target {i} of {len(targets_to_view)}[/bold blue]")
            
            # Display target details
            details = f"[bold]Target ID:[/bold] {target.get('id')}\n"
            details += f"[bold]Name:[/bold] {target.get('name')}\n"
            details += f"[bold]IP Address:[/bold] {target.get('ip_address')}\n"
            details += f"[bold]Source:[/bold] {target.get('source', 'unknown')}\n"
            
            # Add target_type if present
            target_type = target.get('target_type')
            if target_type:
                details += f"[bold]Target Type:[/bold] {target_type}\n"
            
            # Add model if present
            model = target.get('model')
            if model:
                details += f"[bold]Model:[/bold] {model}\n"
            
            details += f"[bold]Description:[/bold] {target.get('description', 'None')}\n"
            details += f"[bold]Updated:[/bold] {target.get('date_updated', target.get('updated_at', 'N/A'))}"
            
            console.print(Panel(
                details,
                title=f"Target: {target.get('name')}",
                border_style="blue"
            ))
        
    except AvenlisError as e:
        console.print(f"[red]Error viewing target(s):[/red] {e}")
        raise click.Abort()


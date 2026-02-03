"""
Collection management commands for the SandStrike CLI.

This module implements prompt collection management for organizing
adversarial prompts into reusable groups/projects.
"""

from typing import List, Optional
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from datetime import datetime

from sandstrike.config import AvenlisConfig
from sandstrike.main_storage import AvenlisStorage
from sandstrike.exceptions import AvenlisError

console = Console()


@click.group(name="collections")
def collections_group() -> None:
    """Manage prompt collections for organized adversarial testing."""
    pass




@collections_group.command(name="create")
@click.option("--id", help="Collection ID (optional, auto-generated if not provided)")
@click.option("--name", "-n", required=True, help="Name for the collection")
@click.option("--description", "-d", help="Description of the collection")
@click.option("--source", "-s", type=click.Choice(['local', 'file']), required=True, help="Source type: local (SQLite) or file (YAML)")
def create_collection(id: Optional[str], name: str, description: Optional[str], source: str) -> None:
    """Create a new prompt collection."""
    
    try:
        config = AvenlisConfig()
        storage_instance = AvenlisStorage(config)
        
        # Generate collection ID if not provided
        if not id:
            collection_id = f"collection_{int(datetime.now().timestamp())}"
        else:
            collection_id = id
        
        if source == 'file':
            created_id = storage_instance.create_yaml_collection(
                name=name,
                description=description,
                collection_id=collection_id
            )
            source_type_display = "YAML file"
        else:
            created_id = storage_instance.create_collection(
                name=name,
                description=description,
                collection_id=collection_id
            )
            source_type_display = "local database"
        
        console.print(f"[green][SUCCESS] Created collection:[/green] {name}")
        console.print(f"[blue]Collection ID:[/blue] {created_id}")
        console.print(f"[blue]Description:[/blue] {description or 'None'}")
        console.print(f"[blue]Source:[/blue] {source_type_display}")
        
        console.print(f"\n[yellow]Next steps:[/yellow]")
        console.print(f"  View collection: [cyan]sandstrike collections list[/cyan]")
        
    except AvenlisError as e:
        console.print(f"[red]Error creating collection:[/red] {e}")
        raise click.Abort()


@collections_group.command(name="list")
@click.option("--source", type=click.Choice(['file', 'local'], case_sensitive=False), help="Filter by source: file (YAML) or local (database)")
def list_collections(source: Optional[str]) -> None:
    """List all prompt collections."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        collections = storage.get_combined_collections()
        
        # Filter by source if specified
        if source:
            source_lower = source.lower()
            filtered_collections = []
            for collection in collections:
                collection_source = collection.get('source', 'local')
                if collection_source == source_lower:
                    filtered_collections.append(collection)
            collections = filtered_collections
        
        if not collections:
            console.print("[yellow]No collections found[/yellow]")
            if source:
                console.print("[dim]Try adjusting your filter criteria[/dim]")
            else:
                console.print("[dim]Create your first collection with:[/dim] [cyan]sandstrike collections create[/cyan]")
            return
        
        # Create table
        table = Table(title="Prompt Collections")
        table.add_column("ID", style="cyan", no_wrap=True, width=20)
        table.add_column("Name", style="magenta", width=25)
        table.add_column("Description", style="white", width=40)
        table.add_column("Source", style="blue", width=8)
        table.add_column("Prompts", style="green", justify="center", width=8)
        
        for collection in collections:
            # Truncate long descriptions
            desc = collection.get('description', '') or ''
            if len(desc) > 37:
                desc = desc[:34] + "..."
            
            # Determine source type
            source_type = collection.get('source', 'unknown')
            if source_type == 'file':
                source_display = "File"
            elif source_type == 'local':
                source_display = "Local"
            else:
                source_display = "Unknown"
            
            table.add_row(
                str(collection['id']),
                collection['name'],
                desc,
                source_display,
                str(collection.get('prompt_count', 0))
            )
        
        console.print(table)
        console.print(f"\n[blue]Total:[/blue] {len(collections)} collections")
        
    except AvenlisError as e:
        console.print(f"[red]Error listing collections:[/red] {e}")
        raise click.Abort()


@collections_group.command(name="delete")
@click.argument("collection_id", type=str)
def delete_collection(collection_id: str) -> None:
    """Delete a prompt collection and all its prompts."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Get collection with full details
        collection_data = storage.get_combined_collection(collection_id)
        if not collection_data:
            console.print(f"[red]Collection {collection_id} not found[/red]")
            return
        
        collection = collection_data.get('collection', {})
        collection_prompts = collection_data.get('prompts', [])
        prompt_count = len(collection_prompts)
        
        # Show deletion details
        console.print(f"[yellow]About to delete collection:[/yellow] {collection.get('name', collection_id)}")
        if collection.get('description'):
            console.print(f"[yellow]Description:[/yellow] {collection.get('description')}")
        collection_type = collection.get('type') or collection.get('source', 'local')
        console.print(f"[yellow]Source:[/yellow] {collection_type}")
        console.print(f"[yellow]Prompts in collection:[/yellow] {prompt_count}")
        
        if prompt_count > 0:
            console.print(f"[red][WARNING]  This will also delete {prompt_count} prompt(s) from this collection[/red]")
        
        # Confirm deletion
        if not Confirm.ask("[red]Are you sure you want to delete this collection?[/red]"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return
        
        # Delete based on source
        collection_type = collection.get('type') or collection.get('source', 'local')
        if collection_type == 'file' or collection_type == 'yaml':
            success = storage.delete_yaml_collection(collection_id)
        else:
            success = storage.delete_collection(collection_id)
        
        if success:
            console.print(f"[green][SUCCESS] Deleted collection:[/green] {collection.get('name', collection_id)}")
        else:
            console.print("[red]Failed to delete collection[/red]")
        
    except AvenlisError as e:
        console.print(f"[red]Error deleting collection:[/red] {e}")
        raise click.Abort()


@collections_group.command(name="add-prompt")
@click.option("--collection-id", "-c", required=True, help="Collection ID to add prompts to")
@click.option("--collection-source", "-cs", type=click.Choice(['local', 'file']), required=True, help="Collection source: local (SQLite) or file (YAML)")
@click.option("--prompt-ids", "-p", required=True, help="Prompt ID(s) separated by commas")
@click.option("--prompt-source", "-ps", type=click.Choice(['local', 'file']), required=True, help="Prompt source: local (SQLite) or file (YAML)")
def add_prompt(collection_id: str, collection_source: str, prompt_ids: str, prompt_source: str) -> None:
    """Add prompt(s) to a collection."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Parse comma-separated prompt IDs
        prompt_id_list = [pid.strip() for pid in prompt_ids.split(',') if pid.strip()]
        if not prompt_id_list:
            console.print("[red]No valid prompt IDs provided[/red]")
            return
        
        # Verify collection exists and matches source
        collection_data = storage.get_combined_collection(collection_id)
        if not collection_data:
            console.print(f"[red]Collection {collection_id} not found[/red]")
            return
        
        collection = collection_data.get('collection', {})
        actual_collection_source = collection.get('source', 'local')
        
        if actual_collection_source != collection_source:
            console.print(f"[red]Collection source mismatch. Collection is '{actual_collection_source}' but specified as '{collection_source}'[/red]")
            return
        
        # Get all prompts and filter by source
        all_prompts = storage.get_all_prompts()
        prompts_by_source = {}
        for prompt in all_prompts:
            prompt_id = str(prompt.get('id', ''))
            prompt_src = prompt.get('source', 'file')
            prompts_by_source[prompt_id] = {
                'prompt': prompt,
                'source': prompt_src
            }
        
        # Validate all prompt IDs exist and match prompt source
        valid_prompt_ids = []
        invalid_prompts = []
        wrong_source_prompts = []
        
        for prompt_id in prompt_id_list:
            if prompt_id not in prompts_by_source:
                invalid_prompts.append(prompt_id)
            elif prompts_by_source[prompt_id]['source'] != prompt_source:
                wrong_source_prompts.append(prompt_id)
            else:
                valid_prompt_ids.append(prompt_id)
        
        if invalid_prompts:
            console.print(f"[red]Prompt(s) not found: {', '.join(invalid_prompts)}[/red]")
            return
        
        if wrong_source_prompts:
            console.print(f"[red]Prompt(s) source mismatch: {', '.join(wrong_source_prompts)}[/red]")
            console.print(f"[yellow]Expected source: {prompt_source}[/yellow]")
            return
        
        # Check which prompts are already in the collection
        collection_prompts = collection_data.get('prompts', [])
        existing_prompt_ids = {str(p.get('id')) for p in collection_prompts}
        new_prompt_ids = [pid for pid in valid_prompt_ids if pid not in existing_prompt_ids]
        already_in_collection = [pid for pid in valid_prompt_ids if pid in existing_prompt_ids]
        
        if already_in_collection:
            console.print(f"[yellow]Prompt(s) already in collection: {', '.join(already_in_collection)}[/yellow]")
        
        if not new_prompt_ids:
            console.print("[yellow]No new prompts to add[/yellow]")
            return
        
        # Show addition details
        console.print(f"[yellow]About to add {len(new_prompt_ids)} prompt(s) to collection:[/yellow] {collection.get('name', collection_id)}")
        console.print(f"[blue]Collection ID:[/blue] {collection_id}")
        console.print(f"[blue]Collection Source:[/blue] {collection_source}")
        console.print(f"[blue]Prompt IDs:[/blue] {', '.join(new_prompt_ids)}")
        console.print(f"[blue]Prompt Source:[/blue] {prompt_source}")
        
        # Add prompts based on collection type and prompt source
        success_count = 0
        failed_prompts = []
        
        if collection_source == 'file' or collection_source == 'yaml':
            # For YAML collections, update the prompt_ids list
            current_prompt_ids = collection.get('prompt_ids', [])
            # Filter out None values and ensure prompt IDs are not already present
            current_prompt_ids = [pid for pid in current_prompt_ids if pid is not None]
            updated_prompt_ids = list(set(current_prompt_ids + new_prompt_ids))  # Use set to avoid duplicates
            success = storage.update_yaml_collection(
                collection_id=collection_id,
                prompt_ids=updated_prompt_ids
            )
            if success:
                success_count = len(new_prompt_ids)
            else:
                failed_prompts = new_prompt_ids
        else:
            # For local/database collections
            if prompt_source == 'file':
                # For file-based prompts, directly update the collection's prompt_ids array
                # since they don't exist in the database
                try:
                    with storage.get_db_session() as db:
                        from sandstrike.main_storage import PromptCollection
                        from sqlalchemy.sql import func
                        collection_obj = db.query(PromptCollection).filter(PromptCollection.id == collection_id).first()
                        if not collection_obj:
                            raise AvenlisError(f"Collection {collection_id} not found")
                        
                        # Get current prompt_ids
                        collection_dict = collection_obj.to_dict()
                        current_prompt_ids = collection_dict.get('prompt_ids', [])
                        if not isinstance(current_prompt_ids, list):
                            current_prompt_ids = []
                        
                        # Add new prompt IDs (avoid duplicates)
                        updated_prompt_ids = list(set(current_prompt_ids + new_prompt_ids))
                        
                        # Update collection
                        collection_obj.prompt_ids = json.dumps(updated_prompt_ids)
                        collection_obj.date_updated = func.now()
                        db.commit()
                        
                        success_count = len(new_prompt_ids)
                except Exception as e:
                    console.print(f"[red]Error updating collection: {e}[/red]")
                    failed_prompts = new_prompt_ids
            else:
                # For local prompts, use the existing method that checks the database
                for prompt_id in new_prompt_ids:
                    try:
                        result = storage.add_prompt_to_collection(collection_id, prompt_id=prompt_id)
                        if result is not None:
                            success_count += 1
                        else:
                            failed_prompts.append(prompt_id)
                    except Exception as e:
                        console.print(f"[red]Error adding prompt {prompt_id}: {e}[/red]")
                        failed_prompts.append(prompt_id)
        
        # Report results
        if success_count > 0:
            console.print(f"[green][SUCCESS] Added {success_count} prompt(s) to collection[/green]")
        if failed_prompts:
            console.print(f"[red]Failed to add prompt(s): {', '.join(failed_prompts)}[/red]")
        
    except AvenlisError as e:
        console.print(f"[red]Error adding prompts:[/red] {e}")
        raise click.Abort()


@collections_group.command(name="remove-prompt")
@click.option("--collection-id", "-c", required=True, help="Collection ID to remove prompts from")
@click.option("--collection-source", "-cs", type=click.Choice(['local', 'file']), required=True, help="Collection source: local (SQLite) or file (YAML)")
@click.option("--prompt-ids", "-p", required=True, help="Prompt ID(s) separated by commas to remove")
def remove_prompt(collection_id: str, collection_source: str, prompt_ids: str) -> None:
    """Remove prompt(s) from a collection."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Parse comma-separated prompt IDs
        prompt_id_list = [pid.strip() for pid in prompt_ids.split(',') if pid.strip()]
        if not prompt_id_list:
            console.print("[red]No valid prompt IDs provided[/red]")
            return
        
        # Verify collection exists and matches source
        collection_data = storage.get_combined_collection(collection_id)
        if not collection_data:
            console.print(f"[red]Collection {collection_id} not found[/red]")
            return
        
        collection = collection_data.get('collection', {})
        actual_collection_source = collection.get('source', 'local')
        
        if actual_collection_source != collection_source:
            console.print(f"[red]Collection source mismatch. Collection is '{actual_collection_source}' but specified as '{collection_source}'[/red]")
            return
        
        # Check which prompts are in the collection
        collection_prompts = collection_data.get('prompts', [])
        existing_prompt_ids = {str(p.get('id')) for p in collection_prompts}
        prompts_to_remove = [pid for pid in prompt_id_list if pid in existing_prompt_ids]
        not_in_collection = [pid for pid in prompt_id_list if pid not in existing_prompt_ids]
        
        if not_in_collection:
            console.print(f"[yellow]Prompt(s) not in collection: {', '.join(not_in_collection)}[/yellow]")
        
        if not prompts_to_remove:
            console.print("[yellow]No prompts to remove[/yellow]")
            return
        
        # Show removal details
        console.print(f"[yellow]About to remove {len(prompts_to_remove)} prompt(s) from collection:[/yellow] {collection.get('name', collection_id)}")
        console.print(f"[blue]Collection ID:[/blue] {collection_id}")
        console.print(f"[blue]Collection Source:[/blue] {collection_source}")
        console.print(f"[blue]Prompt IDs:[/blue] {', '.join(prompts_to_remove)}")
        
        # Confirm removal
        if not Confirm.ask("[red]Are you sure you want to remove these prompt(s) from the collection?[/red]"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return
        
        # Remove prompts based on collection type
        success_count = 0
        failed_prompts = []
        
        if collection_source == 'file' or collection_source == 'yaml':
            # For YAML collections, update the prompt_ids list
            current_prompt_ids = collection.get('prompt_ids', [])
            updated_prompt_ids = [pid for pid in current_prompt_ids if pid not in prompts_to_remove]
            success = storage.update_yaml_collection(
                collection_id=collection_id,
                prompt_ids=updated_prompt_ids
            )
            if success:
                success_count = len(prompts_to_remove)
            else:
                failed_prompts = prompts_to_remove
        else:
            # For local/database collections, remove each prompt
            for prompt_id in prompts_to_remove:
                try:
                    success = storage.remove_prompt_from_collection(collection_id, prompt_id)
                    if success:
                        success_count += 1
                    else:
                        failed_prompts.append(prompt_id)
                except Exception as e:
                    console.print(f"[red]Error removing prompt {prompt_id}: {e}[/red]")
                    failed_prompts.append(prompt_id)
        
        # Report results
        if success_count > 0:
            console.print(f"[green][SUCCESS] Removed {success_count} prompt(s) from collection[/green]")
        if failed_prompts:
            console.print(f"[red]Failed to remove prompt(s): {', '.join(failed_prompts)}[/red]")
        
    except AvenlisError as e:
        console.print(f"[red]Error removing prompts:[/red] {e}")
        raise click.Abort()



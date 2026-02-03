"""
Database management commands for the SandStrike CLI.

This module provides commands for managing the local SQLite database,
including cleanup operations to remove redundant tables.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from sandstrike.config import AvenlisConfig
from sandstrike.main_storage import AvenlisStorage
from sandstrike.exceptions import AvenlisError

console = Console()


@click.group(name="database")
def database_group() -> None:
    """Manage the local SandStrike database."""
    pass


@database_group.command(name="local-wipe")
@click.option("--dry-run", is_flag=True, help="Show what would be removed without actually removing")
def local_wipe(dry_run: bool) -> None:
    """Reset local sqlite to original tables."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Get database path
        db_path = storage.db_path
        
        if not db_path.exists():
            console.print("[yellow]No database found. Nothing to clean up.[/yellow]")
            return
        
        console.print(f"[blue]Database location:[/blue] {db_path}")
        
        # Connect to database
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Define required tables (will be deleted and recreated)
            required_tables = {
                'test_sessions',
                'prompts',
                'prompt_collections',
                'dynamic_variables',
                'targets'
            }
            
            # Define protected tables (known tables that should be kept as-is)
            protected_tables = {
            }
            
            # Define redundant tables (safe to remove)
            redundant_tables = {
                'rapid_scans',
                'rapid_scan_results', 
                'collections_cache',
                'local_adversarial_prompts',
                'local_collections',
                'local_attack_types',
                'local_vulnerability_categories',
                'local_session_configs',
                'prompt_items',  # This appears to be an old table
                'test_results',  # Removed - no longer needed
                'user_settings',  # Removed - no longer needed
                'collection_prompts'  # Removed - redundant with prompt_collections
            }
            
            # Find tables to remove (including required tables for recreation)
            tables_to_remove = []
            tables_to_recreate = []
            tables_to_keep = []
            
            for table in all_tables:
                if table in redundant_tables:
                    tables_to_remove.append(table)
                elif table in required_tables:
                    tables_to_remove.append(table)  # Remove required tables too
                    tables_to_recreate.append(table)  # Mark for recreation
                elif table in protected_tables:
                    tables_to_keep.append(table)  # Keep protected tables as-is
                else:
                    # Unknown table - ask user
                    console.print(f"[yellow]Unknown table found: {table}[/yellow]")
                    if not dry_run and Confirm.ask(f"Remove unknown table '{table}'?"):
                        tables_to_remove.append(table)
                    else:
                        tables_to_keep.append(table)
            
            # Display analysis
            console.print(f"\n[bold cyan]Database Analysis[/bold cyan]")
            
            analysis_table = Table()
            analysis_table.add_column("Table", style="blue", width=30)
            analysis_table.add_column("Status", style="green", width=15)
            analysis_table.add_column("Action", style="yellow", width=20)
            
            for table in sorted(all_tables):
                if table in tables_to_remove and table in tables_to_recreate:
                    analysis_table.add_row(table, "Required", "Will Recreate")
                elif table in tables_to_remove:
                    analysis_table.add_row(table, "Redundant", "Will Remove")
                elif table in protected_tables:
                    analysis_table.add_row(table, "Protected", "Will Keep")
                elif table in tables_to_keep:
                    analysis_table.add_row(table, "Unknown", "Will Keep")
                else:
                    analysis_table.add_row(table, "Unknown", "User Decision")
            
            console.print(analysis_table)
            
            # Show summary
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"  • Total tables: {len(all_tables)}")
            console.print(f"  • Tables to keep: {len(tables_to_keep)}")
            console.print(f"  • Tables to remove: {len(tables_to_remove)}")
            console.print(f"  • Tables to recreate: {len(tables_to_recreate)}")
            
            if not tables_to_remove:
                console.print(f"\n[green][SUCCESS] No tables to remove. Database is already clean![/green]")
                return
            
            # Show tables that will be removed
            if tables_to_remove:
                console.print(f"\n[red]Tables to be removed:[/red]")
                for table in tables_to_remove:
                    if table in tables_to_recreate:
                        console.print(f"  • {table} (will be recreated)")
                    else:
                        console.print(f"  • {table}")
            
            if dry_run:
                console.print(f"\n[yellow]Dry run complete. No changes made.[/yellow]")
                console.print(f"[dim]Run without --dry-run to perform the cleanup.[/dim]")
                return
            
            # Confirmation
            console.print(f"\n[red][WARNING]  This will permanently delete {len(tables_to_remove)} tables![/red]")
            if tables_to_recreate:
                console.print(f"[yellow]Required tables will be recreated with original schema.[/yellow]")
            if not Confirm.ask("[red]Are you sure you want to proceed?[/red]"):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return
            
            # Perform cleanup
            console.print(f"\n[blue]Starting database cleanup...[/blue]")
            
            removed_count = 0
            for table in tables_to_remove:
                console.print(f"[blue]Removing {table}...[/blue]")
                
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    removed_count += 1
                    console.print(f"[green][OK] Removed {table}[/green]")
                except sqlite3.Error as e:
                    console.print(f"[red]Error removing table {table}: {e}[/red]")
            
            # Commit changes immediately
            conn.commit()
            console.print(f"[green][OK] Database changes committed[/green]")
            
            # Recreate required tables
            if tables_to_recreate:
                console.print(f"\n[blue]Recreating required tables...[/blue]")
                
                # Import the storage instance to access table creation
                from sandstrike.main_storage import Base
                
                # Create a proper SQLAlchemy engine for table creation
                from sqlalchemy import create_engine
                engine = create_engine(f'sqlite:///{db_path}')
                
                recreated_count = 0
                for table_name in tables_to_recreate:
                    console.print(f"[blue]Recreating {table_name}...[/blue]")
                    
                    try:
                        # Create the table using SQLAlchemy metadata with proper engine
                        Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables[table_name]])
                        recreated_count += 1
                        console.print(f"[green][OK] Recreated {table_name}[/green]")
                    except Exception as e:
                        console.print(f"[red]Error recreating table {table_name}: {e}[/red]")
                
                console.print(f"[green][OK] Recreated {recreated_count} tables[/green]")
            
            # Verify cleanup
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            remaining_tables = [row[0] for row in cursor.fetchall()]
            
            console.print(f"\n[green][SUCCESS] Database cleanup completed![/green]")
            console.print(f"[blue]Removed:[/blue] {removed_count} tables")
            if tables_to_recreate:
                console.print(f"[blue]Recreated:[/blue] {len(tables_to_recreate)} tables")
            console.print(f"[blue]Remaining:[/blue] {len(remaining_tables)} tables")
            
            # Show remaining tables
            if remaining_tables:
                console.print(f"\n[bold]Remaining tables:[/bold]")
                for table in remaining_tables:
                    console.print(f"  • {table}")
            
            # Verify required tables still exist
            remaining_set = set(remaining_tables)
            still_required = required_tables & remaining_set
            
            if len(still_required) == len(required_tables):
                console.print(f"\n[green][SUCCESS] All required tables are present.[/green]")
            else:
                missing = required_tables - remaining_set
                console.print(f"\n[red][FAILED] Warning: Some required tables are missing:[/red]")
                for table in missing:
                    console.print(f"  • {table}")
            
            try:
                # Test basic operations
                test_storage = AvenlisStorage(config)
                
                # Test session operations
                sessions = test_storage.get_sessions()
                console.print(f"  • Sessions: {len(sessions)} found")
                
                # Test prompt operations  
                prompts = test_storage.get_prompts(limit=5)
                console.print(f"  • Prompts: {len(prompts)} found")
                
                # Test collection operations
                collections = test_storage.get_combined_collections()
                console.print(f"  • Collections: {len(collections)} found")
                
                console.print(f"\n[green][SUCCESS] Database functionality verified![/green]")
                
            except Exception as e:
                console.print(f"\n[red][FAILED] Database functionality test failed: {e}[/red]")
                console.print(f"[yellow]You may need to restore from backup.[/yellow]")
    
    except AvenlisError as e:
        console.print(f"[red]Error during database cleanup:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error during cleanup:[/red] {e}")
        raise click.Abort()


@database_group.command(name="status")
def database_status() -> None:
    """Show current database status and table information."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        db_path = storage.db_path
        
        if not db_path.exists():
            console.print("[yellow]No database found.[/yellow]")
            return
        
        console.print(f"[blue]Database location:[/blue] {db_path}")
        console.print(f"[blue]Database size:[/blue] {db_path.stat().st_size / 1024:.1f} KB")
        
        # Connect to database
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Define table categories
            required_tables = {
                'test_sessions', 'test_results', 'user_settings',
                'prompts', 'prompt_collections', 'collection_prompts',
                'dynamic_variables', 'targets'
            }
            
            protected_tables = {
            }
            
            redundant_tables = {
                'rapid_scans', 'rapid_scan_results', 'collections_cache',
                'local_adversarial_prompts', 'local_collections', 'local_security_types',
                'local_vulnerability_categories', 'local_session_configs', 'prompt_items'
            }
            
            # Categorize tables
            required_found = []
            protected_found = []
            redundant_found = []
            unknown_found = []
            
            for table in all_tables:
                if table in required_tables:
                    required_found.append(table)
                elif table in protected_tables:
                    protected_found.append(table)
                elif table in redundant_tables:
                    redundant_found.append(table)
                else:
                    unknown_found.append(table)
            
            # Display status
            console.print(f"\n[bold cyan]Database Status[/bold cyan]")
            
            status_table = Table()
            status_table.add_column("Category", style="blue", width=20)
            status_table.add_column("Count", style="green", justify="center", width=8)
            status_table.add_column("Tables", style="white", width=50)
            
            status_table.add_row(
                "Required", 
                str(len(required_found)),
                ", ".join(required_found) if required_found else "None"
            )
            
            if protected_found:
                status_table.add_row(
                    "Protected", 
                    str(len(protected_found)),
                    ", ".join(protected_found) if protected_found else "None"
                )
            
            status_table.add_row(
                "Redundant", 
                str(len(redundant_found)),
                ", ".join(redundant_found) if redundant_found else "None"
            )
            
            if unknown_found:
                status_table.add_row(
                    "Unknown", 
                    str(len(unknown_found)),
                    ", ".join(unknown_found)
                )
            
            console.print(status_table)
            
            # Overall status
            if len(redundant_found) == 0:
                console.print(f"\n[green][SUCCESS] Database is clean - no redundant tables found![/green]")
            else:
                console.print(f"\n[yellow][WARNING]  {len(redundant_found)} redundant tables found.[/yellow]")
                console.print(f"[dim]Run 'sandstrike database local-wipe' to clean them up.[/dim]")
            
            # Show record counts
            console.print(f"\n[bold]Record Counts:[/bold]")
            
            counts_table = Table()
            counts_table.add_column("Table", style="blue", width=20)
            counts_table.add_column("Records", style="green", justify="center", width=10)
            
            for table in sorted(all_tables):
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    counts_table.add_row(table, str(count))
                except sqlite3.Error:
                    counts_table.add_row(table, "Error")
            
            console.print(counts_table)
    
    except Exception as e:
        console.print(f"[red]Error checking database status:[/red] {e}")
        raise click.Abort()

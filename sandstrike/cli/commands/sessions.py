"""
Session management commands for the SandStrike CLI.

This module provides comprehensive session management capabilities
matching the React UI functionality.
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.tree import Tree
from rich.text import Text

from sandstrike.config import AvenlisConfig
from sandstrike.main_storage import AvenlisStorage
from sandstrike.exceptions import AvenlisError

console = Console()


@click.group(name="sessions")
def sessions_group() -> None:
    """Manage test sessions and results."""
    pass


@sessions_group.command(name="list")
@click.option("--status", "-s", type=click.Choice(['completed', 'failed', 'cancelled']),
              help="Filter by session status")
@click.option("--source", type=click.Choice(['local', 'file', 'all']), default='all',
              help="Filter by session source (default: all)")
def list_sessions(status: Optional[str], source: str) -> None:
    """List all test sessions."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Get sessions with filters
        sessions = storage.get_sessions()
        
        # Apply status filter if specified
        if status:
            sessions = [s for s in sessions if s.get('status') == status]
        
        # Apply source filter if specified
        if source != 'all':
            sessions = [s for s in sessions if s.get('source') == source]
        
        if not sessions:
            console.print("[yellow]No sessions found[/yellow]")
            if status:
                console.print("[dim]Try adjusting your search criteria[/dim]")
            else:
                console.print("[dim]Use the web UI to run your first security test[/dim]")
            return
        
        # Table format
        table = Table(title="Test Sessions")
        table.add_column("Session ID", style="magenta", width=25)
        table.add_column("Status", style="white", width=12)
        table.add_column("Prompts", style="blue", justify="center", width=10)
        table.add_column("Success Rate", style="yellow", justify="center", width=12)
        table.add_column("Created", style="dim", width=12)
        table.add_column("Source", style="dim", width=8)
        
        for session in sessions:
            # Calculate prompt counts from results array
            results = session.get('results', [])
            total_prompts = len(results) if results else 0
            
            # Count passed/failed prompts
            passed_prompts = 0
            failed_prompts = 0
            error_prompts = 0
            
            if results:
                for result in results:
                    status = result.get('status', '').lower()
                    if status == 'passed':
                        passed_prompts += 1
                    elif status == 'failed':
                        failed_prompts += 1
                    elif status == 'error':
                        error_prompts += 1
            
            # Calculate success rate (passed / total)
            success_rate = f"{(passed_prompts/total_prompts*100):.0f}%" if total_prompts > 0 else "N/A"
            
            # Format date
            created = session.get('created_at', '')
            if created:
                if 'T' in created:
                    created = created.split('T')[0]
                else:
                    created = created[:10] if len(created) >= 10 else created
            
            # Status with color
            status_text = Text(session.get('status', 'unknown').upper())
            status_text.stylize(_get_status_color(session.get('status', 'unknown')))
            
            table.add_row(
                session.get('id', 'Unknown')[:23] + ("..." if len(session.get('id', '')) > 23 else ""),
                status_text,
                str(total_prompts),
                success_rate,
                created,
                session.get('source', 'local')[:6]
            )
        
        console.print(table)
        console.print(f"\n[blue]Total:[/blue] {len(sessions)} sessions")
        
    except AvenlisError as e:
        console.print(f"[red]Error listing sessions:[/red] {e}")
        raise click.Abort()


@sessions_group.command(name="show")
@click.argument("session_id")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed prompt and response information")
def show_session(session_id: str, detailed: bool) -> None:
    """Show detailed information about a session."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        session = storage.get_session(session_id, include_results=True)
        if not session:
            console.print(f"[red]Session '{session_id}' not found[/red]")
            return
        
        # Handle the case where get_session returns a dict with 'session' and 'results' keys
        if isinstance(session, dict) and 'session' in session:
            session_data = session['session']
            results_data = session.get('results', [])
        else:
            session_data = session
            results_data = session.get('results', [])
        
        # Session overview panel
        info_text = f"[bold]{session_data.get('name', 'Unnamed Session')}[/bold]\n\n"
        info_text += f"[blue]ID:[/blue] {session_data.get('id', 'Unknown')}\n"
        info_text += f"[blue]Target:[/blue] {session_data.get('target', 'Unknown')}\n"
        
        if session_data.get('target_model'):
            info_text += f"[blue]Model:[/blue] {session_data['target_model']}\n"
        
        status_color = _get_status_color(session_data.get('status', 'unknown'))
        info_text += f"[blue]Status:[/blue] [{status_color}]{session_data.get('status', 'unknown').upper()}[/{status_color}]\n"
        info_text += f"[blue]Source:[/blue] {session_data.get('source', 'local').title()}\n"
        
        if session_data.get('created_at'):
            # Convert to GMT+8 (Asia/Singapore timezone)
            try:
                created_at_str = session_data['created_at']
                # Parse the ISO format datetime
                if 'T' in created_at_str:
                    # Remove 'Z' if present and parse
                    dt_str = created_at_str.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(dt_str)
                    # Convert to GMT+8
                    gmt8 = timezone(timedelta(hours=8))
                    dt_gmt8 = dt.astimezone(gmt8)
                    # Format as readable string
                    formatted_date = dt_gmt8.strftime('%Y-%m-%d %H:%M:%S GMT+8')
                    info_text += f"[blue]Created:[/blue] {formatted_date}\n"
                else:
                    info_text += f"[blue]Created:[/blue] {created_at_str}\n"
            except Exception:
                # Fallback to original if parsing fails
                info_text += f"[blue]Created:[/blue] {session_data['created_at']}\n"
        
        console.print(Panel(info_text, title="Session Details", border_style="blue"))
        
        # Test summary
        total_prompts = len(results_data) if results_data else 0
        
        # Count passed/failed prompts
        passed_prompts = 0
        failed_prompts = 0
        error_prompts = 0
        
        if results_data:
            for result in results_data:
                status = result.get('status', '').lower()
                if status == 'passed':
                    passed_prompts += 1
                elif status == 'failed':
                    failed_prompts += 1
                elif status == 'error':
                    error_prompts += 1
        
        console.print("\n[bold cyan]Test Summary[/bold cyan]")
        summary_table = Table()
        summary_table.add_column("Metric", style="blue", width=20)
        summary_table.add_column("Count", style="green", justify="center", width=10)
        summary_table.add_column("Percentage", style="yellow", justify="center", width=12)
        
        def calc_percentage(count, total):
            return f"{(count/total*100):.0f}%" if total > 0 else "0%"
        
        summary_table.add_row("Total Prompts", str(total_prompts), "100%")
        summary_table.add_row("Passed", str(passed_prompts), calc_percentage(passed_prompts, total_prompts))
        summary_table.add_row("Failed", str(failed_prompts), calc_percentage(failed_prompts, total_prompts))
        summary_table.add_row("Errors", str(error_prompts), calc_percentage(error_prompts, total_prompts))
        
        console.print(summary_table)
        
        # Security score
        if session_data.get('security_score') is not None:
            score = session_data['security_score']
            score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
            console.print(f"\n[blue]Security Score:[/blue] [{score_color}]{score:.1f}%[/{score_color}]")
        
        # Show detailed prompt and response information if --detailed flag is used
        if detailed and results_data:
            console.print("\n[bold cyan]Detailed Prompt and Response Information[/bold cyan]")
            
            # Load prompts to get severity info
            from sandstrike.storage.yaml_loader import YAMLLoader
            yaml_loader = YAMLLoader()
            all_prompts = yaml_loader.load_adversarial_prompts()
            
            # Ensure all_prompts is a list
            if not all_prompts or not isinstance(all_prompts, list):
                all_prompts = []
            
            # Create a lookup dictionary for prompt_id -> severity
            prompt_lookup = {}
            for prompt in all_prompts:
                if not prompt or not isinstance(prompt, dict):
                    continue
                prompt_id = prompt.get('id')
                if prompt_id:
                    prompt_lookup[prompt_id] = {
                        'severity': str(prompt.get('severity') or 'N/A')
                    }
            
            details_table = Table()
            details_table.add_column("Prompt ID", style="cyan", width=15)
            details_table.add_column("Status", style="white", width=10)
            details_table.add_column("Severity", style="bold white", width=10)
            details_table.add_column("Prompt Tested", style="yellow", width=None)
            details_table.add_column("Response", style="white", width=None)
            
            for result in results_data[:20]:  # Show first 20 results
                status_text = Text(result.get('status', 'unknown').upper())
                status_text.stylize(_get_status_color(result.get('status', 'unknown')))
                
                # Look up severity for this prompt
                prompt_id = result.get('prompt_id', 'Unknown')
                vuln_info = prompt_lookup.get(prompt_id, {
                    'severity': 'N/A'
                })
                
                # Format severity with color coding
                severity_str = str(vuln_info.get('severity', 'N/A') or 'N/A')
                severity_text = Text(severity_str.upper())
                severity_level = severity_str.lower()
                if severity_level == 'high':
                    severity_text.stylize("red")
                elif severity_level == 'medium':
                    severity_text.stylize("yellow")
                elif severity_level == 'low':
                    severity_text.stylize("green")
                
                # Show full prompt and response without truncation
                prompt_text = result.get('prompt', '') or 'N/A'
                response_text = result.get('response', '') or 'N/A'
                
                details_table.add_row(
                    prompt_id,
                    status_text,
                    severity_text,
                    prompt_text,
                    response_text
                )
            
            console.print(details_table)
            
            if len(results_data) > 20:
                console.print(f"[dim]Showing first 20 of {len(results_data)} detailed results.[/dim]")
        
        
    except AvenlisError as e:
        console.print(f"[red]Error showing session:[/red] {e}")
        raise click.Abort()

def _get_status_color(status: str) -> str:
    """Get color for session status."""
    status_colors = {
        'completed': 'green',
        'running': 'yellow',
        'failed': 'red',
        'cancelled': 'dim',
        'pending': 'blue'
    }
    return status_colors.get(status.lower(), 'white')
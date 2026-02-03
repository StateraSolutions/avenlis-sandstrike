"""
Prompt management commands for the SandStrike CLI.

This module provides comprehensive prompt management capabilities
matching the React UI functionality.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.text import Text

from sandstrike.config import AvenlisConfig
from sandstrike.main_storage import AvenlisStorage
from sandstrike.exceptions import AvenlisError

console = Console()


def _format_mapping(values: Optional[List[Any]]) -> str:
    """Return formatted mapping text, gracefully handling null entries."""
    if not values:
        return 'N/A'
    sanitized = [str(item).strip() for item in values if item is not None and str(item).strip()]
    if not sanitized:
        return 'N/A'
    return ',\n'.join(sanitized)


@click.group(name="prompts")
def prompts_group() -> None:
    """Manage adversarial prompts library."""
    pass


@prompts_group.command(name="create")
@click.option("--id", "prompt_id", required=True, help="Unique prompt ID (required)")
@click.option("--technique", "-t", required=True, help="Attack technique (required, e.g., prompt_injection, prompt_probing)")
@click.option("--category", "-c", required=True, help="Vulnerability category (required, e.g., system_prompt_leakage, violence_and_self_harm)")
@click.option("--text", "-p", required=True, help="Prompt text (required)")
@click.option("--source", "-s", type=click.Choice(['file', 'local'], case_sensitive=False), help="Storage source (required): file (YAML) or local (SQLite database)")
@click.option("--target-file", help="Target YAML file name (optional, only used when --source is 'file'). Default: adversarial_prompts.yaml")
@click.option("--subcategory", help="Vulnerability subcategory (optional, e.g., physical_harm, personal_data)")
@click.option("--severity", default="medium", type=click.Choice(['low', 'medium', 'high', 'critical'], case_sensitive=False), help="Severity level (optional, default: medium)")
@click.option("--atlas", multiple=True, help="MITRE ATLAS mapping IDs (optional, e.g., AML.T0051). Can be specified multiple times.")
@click.option("--owasp", multiple=True, help="OWASP Top 10 LLM mappings (optional, e.g., LLM01:2025). Can be specified multiple times.")
def create_prompt(prompt_id: str, technique: str, category: str, text: str,
                 source: Optional[str], target_file: Optional[str], subcategory: Optional[str], 
                 severity: str, atlas: tuple, owasp: tuple) -> None:
    """Create a new adversarial prompt.
    
    Required fields: --id, --technique, --category, --text, --source
    Optional fields: --target-file (when --source is 'file'), --subcategory, --severity, --atlas, --owasp
    """
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Prompt for source if not provided
        if not source:
            source = Prompt.ask(
                "[yellow]Storage source (required):[/yellow]",
                choices=['file', 'local'],
                default='local'
            )
        
        # Normalize source to lowercase
        source = source.lower()
        
        # If source is 'file', prompt for target_file if not provided
        if source == 'file' and not target_file:
            # Get available prompt files to show as suggestions
            from sandstrike.storage.yaml_loader import yaml_loader
            available_files = yaml_loader.get_available_prompt_files()
            
            if available_files:
                console.print("[blue]Available prompt files:[/blue]")
                for i, file in enumerate(available_files, 1):
                    console.print(f"  [cyan]{i}.[/cyan] {file}")
                console.print(f"  [cyan]new.[/cyan] Create new file")
                console.print("")
            
            # Prompt for file name
            if available_files:
                file_choice = Prompt.ask(
                    "[yellow]Select file (enter number, filename, or 'new' for new file):[/yellow]"
                )
                
                # Handle numeric choice
                if file_choice.isdigit():
                    choice_num = int(file_choice)
                    if 1 <= choice_num <= len(available_files):
                        target_file = available_files[choice_num - 1]
                    else:
                        console.print(f"[red]Invalid choice. Please enter a number between 1 and {len(available_files)}, a filename, or 'new'[/red]")
                        raise click.Abort()
                elif file_choice.lower() == 'new':
                    # Prompt for new file name
                    target_file = Prompt.ask(
                        "[yellow]Enter new file name (e.g., my_prompts.yaml):[/yellow]"
                    )
                    # Ensure .yaml extension
                    if not target_file.endswith('.yaml') and not target_file.endswith('.yml'):
                        target_file += '.yaml'
                else:
                    # User entered a filename directly
                    target_file = file_choice
                    # Ensure .yaml extension if not present
                    if not target_file.endswith('.yaml') and not target_file.endswith('.yml'):
                        target_file += '.yaml'
            else:
                # No existing files, prompt for file name
                target_file = Prompt.ask(
                    "[yellow]Enter file name (e.g., adversarial_prompts.yaml):[/yellow]"
                )
                # Ensure .yaml extension if not present
                if not target_file.endswith('.yaml') and not target_file.endswith('.yml'):
                    target_file += '.yaml'
        
        # Normalize severity to lowercase (database uses lowercase)
        severity_normalized = severity.lower()
        
        # Create prompt data
        prompt_data = {
            'id': prompt_id,
            'attack_technique': technique,
            'vuln_category': category,
            'vuln_subcategory': subcategory or '',
            'prompt': text,
            'severity': severity_normalized,
            'mitreatlasmapping': list(atlas) if atlas else [],
            'owasp_top10_llm_mapping': list(owasp) if owasp else []
        }
        
        # Store prompt based on source
        if source == 'file':
            # Save to YAML file
            prompt_id_result = storage.create_yaml_prompt(
                prompt_id=prompt_id,
                attack_technique=technique,
                prompt=text,
                vuln_category=category,
                vuln_subcategory=subcategory,
                severity=severity_normalized,
                mitreatlasmapping=list(atlas) if atlas else [],
                owasp_top10_llm_mapping=list(owasp) if owasp else [],
                target_file=target_file
            )
            
            if prompt_id_result:
                console.print(f"[green][SUCCESS] Created prompt:[/green] {prompt_id}")
                console.print(f"[blue]Saved to:[/blue] YAML file")
                if target_file:
                    console.print(f"[blue]File:[/blue] {target_file}")
                else:
                    console.print(f"[blue]File:[/blue] adversarial_prompts.yaml")
                console.print(f"[blue]Technique:[/blue] {technique}")
                console.print(f"[blue]Category:[/blue] {category}")
                if subcategory:
                    console.print(f"[blue]Subcategory:[/blue] {subcategory}")
                console.print(f"[blue]Severity:[/blue] {severity_normalized.capitalize()}")
                if atlas:
                    console.print(f"[blue]MITRE ATLAS:[/blue] {', '.join(atlas)}")
                if owasp:
                    console.print(f"[blue]OWASP Top 10 LLM:[/blue] {', '.join(owasp)}")
                
                console.print(f"\n[yellow]Next steps:[/yellow]")
                console.print(f"  View prompt: [cyan]sandstrike prompts view {prompt_id}[/cyan]")
                console.print(f"  Test prompt: [cyan]Use web UI to test prompt[/cyan]")
            else:
                console.print(f"[red]Failed to create prompt in YAML file. ID may already exist.[/red]")
        else:
            # Store in local database
            success = storage.create_prompt(prompt_data)
            if success:
                console.print(f"[green][SUCCESS] Created prompt:[/green] {prompt_id}")
                console.print(f"[blue]Stored in:[/blue] local SQLite database")
                console.print(f"[blue]Technique:[/blue] {technique}")
                console.print(f"[blue]Category:[/blue] {category}")
                if subcategory:
                    console.print(f"[blue]Subcategory:[/blue] {subcategory}")
                console.print(f"[blue]Severity:[/blue] {severity_normalized.capitalize()}")
                if atlas:
                    console.print(f"[blue]MITRE ATLAS:[/blue] {', '.join(atlas)}")
                if owasp:
                    console.print(f"[blue]OWASP Top 10 LLM:[/blue] {', '.join(owasp)}")
                
                console.print(f"\n[yellow]Next steps:[/yellow]")
                console.print(f"  View prompt: [cyan]sandstrike prompts view {prompt_id}[/cyan]")
                console.print(f"  Test prompt: [cyan]Use web UI to test prompt[/cyan]")
            else:
                console.print(f"[red]Failed to create prompt. ID may already exist.[/red]")
            
    except AvenlisError as e:
        console.print(f"[red]Error creating prompt:[/red] {e}")
        raise click.Abort()


@prompts_group.command(name="list")
@click.option("--category", "-c", help="Filter by vulnerability category")
@click.option("--subcategory", "-sc", help="Filter by vulnerability subcategory")
@click.option("--technique", "-t", help="Filter by attack technique")
@click.option("--source", "-s", type=click.Choice(['all', 'local', 'file']), default='all', help="Filter by source (default: all)")
@click.option("--limit", "-l", type=int, default=50, help="Maximum number of prompts to show")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed view with prompt preview")
def list_prompts(category: Optional[str], subcategory: Optional[str], technique: Optional[str],
                source: str, limit: int, detailed: bool) -> None:
    """List all adversarial prompts."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Get prompts with filters
        prompts = storage.get_prompts(
            category=category,
            subcategory=subcategory,
            technique=technique,
            limit=limit
        )
        
        # Filter by source if specified
        if source != 'all':
            filtered_prompts = []
            for prompt in prompts:
                prompt_source = prompt.get('source', 'file')  # Default to 'file' if not specified
                if source == 'local' and prompt_source == 'local':
                    filtered_prompts.append(prompt)
                elif source == 'file' and prompt_source == 'file':
                    filtered_prompts.append(prompt)
            prompts = filtered_prompts
        
        if not prompts:
            console.print("[yellow]No prompts found[/yellow]")
            if category or technique:
                console.print("[dim]Try adjusting your search criteria[/dim]")
            else:
                console.print("[dim]Create your first prompt with:[/dim] [cyan]sandstrike prompts create[/cyan]")
            return
        
        # Table format - different structure for detailed view
        if detailed:
            table = Table(title="Adversarial Prompts - Detailed View")
            table.add_column("Prompt ID", style="cyan", no_wrap=True, width=15)
            table.add_column("Prompt Preview", width=50)
            table.add_column("Severity", style="bold white", width=15)
            table.add_column("Source", width=10)
        else:
            table = Table(title="Adversarial Prompts")
            table.add_column("Prompt ID", style="cyan", no_wrap=True, width=15)
            table.add_column("Attack Technique", width=20)
            table.add_column("Vulnerability Category", width=18)
            table.add_column("Severity", style="bold white", width=15)
            table.add_column("OWASP Top 10 LLM Mapping", width=20)
            table.add_column("MITRE ATLAS Mapping", width=20)
            table.add_column("Source", width=10)
        
        for prompt in prompts:
            # Preview text - handle both 'prompt' and 'prompt_text' fields
            prompt_text = prompt.get('prompt_text') or prompt.get('prompt', '')
            preview = prompt_text[:37] + "..." if len(prompt_text) > 40 else prompt_text
            preview = preview.replace('\n', ' ')
            
            # Format OWASP and MITRE mappings
            owasp_mappings = prompt.get('owasp_top10_llm_mapping', [])
            mitre_mappings = prompt.get('mitreatlasmapping', [])
            
            owasp_text = _format_mapping(owasp_mappings)
            mitre_text = _format_mapping(mitre_mappings)
            
            vuln_category = prompt.get('vulnerability_category') or prompt.get('vuln_category', '')
            vuln_subcategory = prompt.get('vulnerability_subcategory') or prompt.get('vuln_subcategory', '')
            
            # Get severity and format with color coding
            severity = prompt.get('severity', 'N/A')
            severity_level = severity.lower()
            if severity_level == 'high':
                severity_display = f"[red]{severity.upper()}[/red]"
            elif severity_level == 'medium':
                severity_display = f"[yellow]{severity.upper()}[/yellow]"
            elif severity_level == 'low':
                severity_display = f"[green]{severity.upper()}[/green]"
            else:
                severity_display = severity.upper()
            
            # Get source
            source = prompt.get('source', 'local')
            
            if detailed:
                # Detailed view: Prompt ID, Prompt Preview, Severity, Source
                table.add_row(
                    prompt['id'],
                    preview,
                    severity_display,
                    source
                )
            else:
                # Normal view: all columns - use styled severity text for color coding
                table.add_row(
                    prompt['id'],
                    prompt['attack_technique'],
                    vuln_category,
                    severity_display,
                    owasp_text,
                    mitre_text,
                    source
                )
        
        console.print(table, markup=True)
        console.print(f"\n[blue]Total:[/blue] {len(prompts)} prompts")
        
        if len(prompts) == limit:
            console.print(f"[dim]Showing first {limit} results. Use --limit to see more.[/dim]")
        
    except AvenlisError as e:
        console.print(f"[red]Error listing prompts:[/red] {e}")
        raise click.Abort()


@prompts_group.command(name="view")
@click.argument("prompt_id")
@click.option("--details", "-d", is_flag=True, help="Show usage statistics and related sessions")
def view_prompt(prompt_id: str, details: bool) -> None:
    """Show detailed information about a prompt."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        prompt = storage.get_prompt(prompt_id)
        if not prompt:
            console.print(f"[red]Prompt '{prompt_id}' not found[/red]")
            return
        
        # Prompt details panel
        info_text = f"[blue]Prompt ID:[/blue] {prompt['id']}\n\n"
        vuln_category = prompt.get('vulnerability_category') or prompt.get('vuln_category', 'Unknown')
        vuln_subcategory = prompt.get('vulnerability_subcategory') or prompt.get('vuln_subcategory', '')
        
        info_text += f"[blue]Attack Technique:[/blue] {prompt['attack_technique']}\n"
        info_text += f"[blue]Vulnerability Category:[/blue] {vuln_category}\n"
        
        if vuln_subcategory:
            info_text += f"[blue]Vulnerability Subcategory:[/blue] {vuln_subcategory}\n"
        
        if prompt.get('created_at'):
            info_text += f"[blue]Created:[/blue] {prompt['created_at'][:10]}\n"
        
        # Framework mappings
        mitre_mappings = prompt.get('mitreatlasmapping', [])
        owasp_mappings = prompt.get('owasp_top10_llm_mapping', [])
        
        if mitre_mappings:
            info_text += f"[blue]MITRE ATLAS Mapping:[/blue] {', '.join(mitre_mappings)}\n"
        
        if owasp_mappings:
            info_text += f"[blue]OWASP Top 10 LLM Mapping:[/blue] {', '.join(owasp_mappings)}\n"
        
        console.print(Panel(info_text, title="Prompt Details", border_style="blue"))
        
        # Prompt text
        console.print("\n[bold cyan]Prompt Text[/bold cyan]")
        prompt_text = prompt.get('prompt_text') or prompt.get('prompt', '')
        syntax = Syntax(prompt_text, "text", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, border_style="cyan"))
        
        # Usage statistics and related sessions
        if details:
            console.print("\n[bold cyan]Usage Statistics[/bold cyan]")
            
            # Get all sessions from both sources
            all_sessions = storage.get_combined_sessions()
            
            # Count usage statistics
            usage_count = 0
            success_count = 0
            failure_count = 0
            error_count = 0
            related_sessions = []
            last_used = None
            
            for session in all_sessions:
                results = session.get('results', [])
                if results:
                    for result in results:
                        if result.get('prompt_id') == prompt_id:
                            usage_count += 1
                            related_sessions.append(session)
                            
                            # Track status counts
                            status = result.get('status', '').lower()
                            if status == 'passed':
                                success_count += 1
                            elif status == 'failed':
                                failure_count += 1
                            elif status == 'error':
                                error_count += 1
                            
                            # Track last used date
                            session_date = session.get('created_at') or session.get('started_at')
                            if session_date and (not last_used or session_date > last_used):
                                last_used = session_date
            
            # Calculate success rate
            success_rate = (success_count / usage_count * 100) if usage_count > 0 else 0
            
            # Display statistics
            stats_table = Table()
            stats_table.add_column("Metric", width=20)
            stats_table.add_column("Value", width=15)
            
            stats_table.add_row("Times Used", str(usage_count))
            stats_table.add_row("Success Rate", f"{success_rate:.1f}%")
            stats_table.add_row("Successful Tests", str(success_count))
            stats_table.add_row("Failed Tests", str(failure_count))
            stats_table.add_row("Error Tests", str(error_count))
            stats_table.add_row("Last Used", last_used[:10] if last_used else "Never")
            
            console.print(stats_table)
            
            # Show related sessions
            if related_sessions:
                console.print("\n[bold cyan]Related Sessions[/bold cyan]")
                sessions_table = Table()
                sessions_table.add_column("Result", style="bold white", width=8)
                sessions_table.add_column("Session ID", width=20)
                sessions_table.add_column("Name", width=30)
                sessions_table.add_column("Status", style="green", width=12)
                sessions_table.add_column("Date", width=12)
                
                # Sort sessions by date (newest first)
                related_sessions.sort(key=lambda x: x.get('created_at', x.get('started_at', '')), reverse=True)
                
                for session in related_sessions[:10]:  # Show max 10 sessions
                    # Find the result for this specific prompt in this session
                    session_results = session.get('results', [])
                    prompt_result = None
                    for result in session_results:
                        if result.get('prompt_id') == prompt_id:
                            prompt_result = result
                            break
                    
                    # Get the result status
                    if prompt_result:
                        result_status = prompt_result.get('status', 'unknown').upper()
                        # Color code the result
                        if result_status == 'PASSED':
                            result_display = "[green]PASSED[/green]"
                        elif result_status == 'FAILED':
                            result_display = "[red]FAILED[/red]"
                        elif result_status == 'ERROR':
                            result_display = "[yellow]ERROR[/yellow]"
                        else:
                            result_display = f"[dim]{result_status}[/dim]"
                    else:
                        result_display = "[dim]N/A[/dim]"
                    
                    sessions_table.add_row(
                        result_display,
                        session.get('id', 'Unknown'),
                        session.get('name', 'Unknown'),
                        session.get('status', 'Unknown'),
                        (session.get('created_at', '') or session.get('started_at', ''))[:10] if session.get('created_at') or session.get('started_at') else ''
                    )
                
                console.print(sessions_table)
                
                if len(related_sessions) > 10:
                    console.print(f"[dim]Showing first 10 of {len(related_sessions)} related sessions.[/dim]")
            else:
                console.print("\n[bold cyan]Related Sessions[/bold cyan]")
                console.print("[yellow]No related sessions found[/yellow]")
        
        # Available commands
        console.print(f"\n[yellow]Available commands:[/yellow]")
        console.print(f"  Test prompt: [cyan]Use web UI to test prompt[/cyan]")
        console.print(f"  Delete prompt: [cyan]sandstrike prompts delete {prompt_id}[/cyan]")
        
    except AvenlisError as e:
        console.print(f"[red]Error showing prompt:[/red] {e}")
        raise click.Abort()


@prompts_group.command(name="delete")
@click.argument("prompt_id")
@click.option("--source", "-s", type=click.Choice(['auto', 'local', 'file'], case_sensitive=False), default='auto', help="Source to delete from: auto (detect), local (database), or file (YAML). Default: auto")
def delete_prompt(prompt_id: str, source: str) -> None:
    """Delete an adversarial prompt."""
    
    try:
        config = AvenlisConfig()
        storage = AvenlisStorage(config)
        
        # Get all prompts to check for duplicates
        all_prompts = storage.get_all_prompts()
        matching_prompts = [p for p in all_prompts if str(p.get('id')) == str(prompt_id)]
        
        if not matching_prompts:
            console.print(f"[red]Prompt '{prompt_id}' not found[/red]")
            return
        
        # Check if prompt exists in multiple sources
        sources_found = set(p.get('source', 'local') for p in matching_prompts)
        all_matching_prompts = matching_prompts.copy()  # Keep original list for 'all' option
        
        # If source is auto and multiple sources found, ask user to choose
        if source.lower() == 'auto' and len(sources_found) > 1:
            console.print(f"[yellow][WARNING]  Prompt '{prompt_id}' found in multiple sources:[/yellow]")
            console.print("")
            
            # Show details for each source
            for i, prompt in enumerate(all_matching_prompts, 1):
                prompt_source = prompt.get('source', 'local')
                source_file = prompt.get('source_file', 'N/A')
                technique = prompt.get('attack_technique', 'Unknown')
                prompt_text = prompt.get('prompt_text') or prompt.get('prompt', '')
                preview = prompt_text[:60] + "..." if len(prompt_text) > 60 else prompt_text
                
                console.print(f"  [cyan]{i}.[/cyan] [bold]{prompt_source.upper()}[/bold]")
                console.print(f"      Technique: {technique}")
                if prompt_source == 'file':
                    console.print(f"      File: {source_file}")
                console.print(f"      Preview: {preview}")
                console.print("")
            
            # Ask user to choose
            while True:
                choice = Prompt.ask(
                    f"[yellow]Which source would you like to delete from?[/yellow] (1-{len(all_matching_prompts)} or 'all' for both)",
                    default="1"
                )
                
                if choice.lower() == 'all':
                    # Delete from all sources
                    prompt_source = 'all'
                    matching_prompts = all_matching_prompts  # Use all prompts
                    break
                elif choice.isdigit() and 1 <= int(choice) <= len(all_matching_prompts):
                    selected_prompt = all_matching_prompts[int(choice) - 1]
                    prompt_source = selected_prompt.get('source', 'local')
                    source_file = selected_prompt.get('source_file')
                    matching_prompts = [selected_prompt]  # Only delete the selected one
                    break
                else:
                    console.print(f"[red]Invalid choice. Please enter 1-{len(all_matching_prompts)} or 'all'[/red]")
        else:
            # Single source or user specified source
            if source.lower() == 'auto':
                # Use the first (or only) prompt's source
                prompt = matching_prompts[0]
                prompt_source = prompt.get('source', 'local')
                source_file = prompt.get('source_file')
            else:
                # User specified source - find matching prompt
                prompt_source = source.lower()
                matching_prompt = next((p for p in matching_prompts if p.get('source', 'local') == prompt_source), None)
                if not matching_prompt:
                    console.print(f"[red]Prompt '{prompt_id}' not found in source '{prompt_source}'[/red]")
                    if len(sources_found) > 0:
                        console.print(f"[yellow]Available sources: {', '.join(sources_found)}[/yellow]")
                    return
                prompt = matching_prompt
                source_file = prompt.get('source_file')
                matching_prompts = [prompt]
        
        # Show deletion details
        if prompt_source == 'all':
            console.print(f"[yellow]About to delete prompt '{prompt_id}' from all sources:[/yellow]")
            for prompt in matching_prompts:
                src = prompt.get('source', 'local')
                src_file = prompt.get('source_file', '')
                technique = prompt.get('attack_technique', 'Unknown')
                if src_file:
                    console.print(f"  - {src} (File: {src_file}, Technique: {technique})")
                else:
                    console.print(f"  - {src} (Technique: {technique})")
        else:
            prompt = matching_prompts[0]
            console.print(f"[yellow]About to delete prompt:[/yellow] {prompt_id}")
            console.print(f"[yellow]Technique:[/yellow] {prompt.get('attack_technique', 'Unknown')}")
            console.print(f"[yellow]Source:[/yellow] {prompt_source}")
            if source_file:
                console.print(f"[yellow]File:[/yellow] {source_file}")
            prompt_text = prompt.get('prompt_text') or prompt.get('prompt', '')
            console.print(f"[dim]Preview: {prompt_text[:100]}...[/dim]")
        
        # Check usage (if method exists)
        try:
            if hasattr(storage, 'get_prompt_usage_stats'):
                usage_stats = storage.get_prompt_usage_stats(prompt_id)
                if usage_stats and usage_stats.get('usage_count', 0) > 0:
                    console.print(f"[yellow][WARNING]  This prompt has been used {usage_stats['usage_count']} times[/yellow]")
        except Exception:
            # Ignore if usage stats check fails
            pass
        
        # Confirm deletion
        if not Confirm.ask("[red]Are you sure you want to delete this prompt?[/red]"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return
        
        # Delete based on source(s)
        if prompt_source == 'all':
            # Delete from all sources
            success_count = 0
            for prompt in matching_prompts:
                src = prompt.get('source', 'local')
                src_file = prompt.get('source_file')
                if src == 'local':
                    if storage.delete_prompt(prompt_id):
                        success_count += 1
                elif src == 'file':
                    if storage.delete_yaml_prompt(prompt_id, src_file):
                        success_count += 1
            
            if success_count == len(matching_prompts):
                console.print(f"[green][SUCCESS] Deleted prompt '{prompt_id}' from all sources[/green]")
            else:
                console.print(f"[yellow][WARNING]  Deleted prompt '{prompt_id}' from {success_count} of {len(matching_prompts)} sources[/yellow]")
        else:
            # Delete from single source
            success = False
            if prompt_source == 'local':
                success = storage.delete_prompt(prompt_id)
            elif prompt_source == 'file':
                success = storage.delete_yaml_prompt(prompt_id, source_file)
            else:
                # Try both if source is unclear
                console.print(f"[yellow]Unknown source '{prompt_source}', trying local deletion...[/yellow]")
                success = storage.delete_prompt(prompt_id)
                if not success:
                    console.print(f"[yellow]Local deletion failed, trying YAML deletion...[/yellow]")
                    success = storage.delete_yaml_prompt(prompt_id, source_file)
            
            if success:
                console.print(f"[green][SUCCESS] Deleted prompt:[/green] {prompt_id} (from {prompt_source})")
            else:
                console.print(f"[red]Failed to delete prompt from {prompt_source}[/red]")
                console.print("[yellow]Tip: Try specifying --source explicitly[/yellow]")
        
    except AvenlisError as e:
        console.print(f"[red]Error deleting prompt:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise click.Abort()

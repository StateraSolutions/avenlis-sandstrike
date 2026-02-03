"""
SandStrike Reports CLI commands.

This module provides CLI commands for generating PDF reports from session results.
Reports are only available for paid users.
"""

import os
import click
import json
import requests
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from sandstrike.sandstrike_auth import get_sandstrike_auth, load_env_file
from sandstrike.exceptions import AvenlisError

console = Console()

# Load .env file when module is imported
load_env_file()


@click.group(name="reports")
def reports_group() -> None:
    """Generate HTML reports from SandStrike session results (Paid Users Only)."""
    pass


def _fetch_report_code(api_key, platform_base_url, report_type):
    """Fetch report generation code from production server."""
    try:
        response = requests.get(
            f"{platform_base_url}/reports/code",
            headers={
                'X-API-Key': api_key,
                'Content-Type': 'application/json'
            },
            params={'apiKey': api_key, 'reportType': report_type},
            timeout=30
        )
        
        if response.status_code == 401:
            raise AvenlisError("Invalid API key. Please verify your API key.")
        elif response.status_code == 403:
            raise AvenlisError("Reports feature requires a Pro subscription.")
        elif response.status_code != 200:
            error_msg = response.json().get('error', 'Failed to fetch report code')
            raise AvenlisError(f"Failed to fetch report code: {error_msg}")
        
        result = response.json()
        if not result.get('success'):
            raise AvenlisError(result.get('error', 'Failed to fetch report code'))
        
        return result.get('code', {})
        
    except requests.exceptions.RequestException as e:
        raise AvenlisError(f"Network error while getting report code: {str(e)}")


def _setup_temporary_report_code(code_package, temp_dir):
    """Set up temporary report generation code files."""
    import shutil
    
    # Create temporary directory structure
    reports_temp_dir = Path(temp_dir) / 'reports_temp'
    if reports_temp_dir.exists():
        shutil.rmtree(reports_temp_dir)
    reports_temp_dir.mkdir(parents=True, exist_ok=True)
    
    templates_dir = reports_temp_dir / 'templates'
    static_dir = reports_temp_dir / 'static'
    css_dir = static_dir / 'css'
    js_dir = static_dir / 'js'
    
    # Ensure all directories are created with parents
    templates_dir.mkdir(parents=True, exist_ok=True)
    css_dir.mkdir(parents=True, exist_ok=True)
    js_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify directories were created
    if not templates_dir.exists():
        raise AvenlisError(f"Failed to create templates directory: {templates_dir}")
    if not static_dir.exists():
        raise AvenlisError(f"Failed to create static directory: {static_dir}")
    
    # Write html_generator.py
    html_generator_path = reports_temp_dir / 'html_generator.py'
    with open(html_generator_path, 'w', encoding='utf-8') as f:
        f.write(code_package.get('html_generator', ''))
    
    # Verify html_generator.py was written
    if not html_generator_path.exists():
        raise AvenlisError(f"Failed to write html_generator.py: {html_generator_path}")
    
    # Write templates (handle both / and \ path separators)
    for rel_path, content in code_package.get('templates', {}).items():
        # Normalize path separators
        normalized_path = rel_path.replace('\\', '/')
        template_path = templates_dir / normalized_path
        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Write CSS files
    for rel_path, content in code_package.get('static', {}).get('css', {}).items():
        normalized_path = rel_path.replace('\\', '/')
        css_path = css_dir / normalized_path
        css_path.parent.mkdir(parents=True, exist_ok=True)
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Write JS files
    for rel_path, content in code_package.get('static', {}).get('js', {}).items():
        normalized_path = rel_path.replace('\\', '/')
        js_path = js_dir / normalized_path
        js_path.parent.mkdir(parents=True, exist_ok=True)
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return reports_temp_dir


def _cleanup_temporary_code(temp_dir):
    """Clean up temporary report generation code."""
    try:
        import shutil
        reports_temp_dir = Path(temp_dir) / 'reports_temp'
        if reports_temp_dir.exists():
            shutil.rmtree(reports_temp_dir)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not clean up temporary files: {e}[/yellow]")


def generate_html_report(sessions_data, report_type):
    """Generate HTML report content by fetching code from server, using it locally, then cleaning up."""
    
    temp_dir = None
    try:
        from sandstrike.sandstrike_auth import get_sandstrike_auth
        import tempfile
        import sys
        
        # Get API key
        auth = get_sandstrike_auth()
        api_key = auth.get_stored_api_key()
        if not api_key:
            api_key = os.getenv('AVENLIS_API_KEY')
        
        if not api_key:
            raise AvenlisError("API key required for report generation. Please configure your API key.")
        
        # Get Otterback base URL from environment or use default
        platform_base_url = os.getenv('AVENLIS_PLATFORM_BASE_URL', 'https://avenlis.staterasolv.com/api')
        
        # Fetch code from server
        code_package = _fetch_report_code(api_key, platform_base_url, report_type)
        
        # Set up temporary directory
        temp_dir = tempfile.mkdtemp(prefix='sandstrike_reports_')
        reports_temp_dir = _setup_temporary_report_code(code_package, temp_dir)
        
        # Add temporary directory to Python path
        sys.path.insert(0, str(reports_temp_dir))
        
        try:
            # Import and use the generator
            from html_generator import HTMLReportGenerator
            
            generator = HTMLReportGenerator()
            
            # Generate report
            if report_type == 'overview':
                html_content = generator.generate_overview_report(sessions_data)
            elif report_type == 'detailed':
                html_content = generator.generate_detailed_report(sessions_data)
            elif report_type == 'executive':
                html_content = generator.generate_executive_report(sessions_data)
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            return html_content
            
        finally:
            # Remove from path
            if str(reports_temp_dir) in sys.path:
                sys.path.remove(str(reports_temp_dir))
            
            # Clean up temporary files
            _cleanup_temporary_code(temp_dir)
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
        
    except requests.exceptions.RequestException as e:
        raise AvenlisError(f"Network error while generating report: {str(e)}")
    except Exception as e:
        # Ensure cleanup even on error
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
        if isinstance(e, AvenlisError):
            raise
        raise AvenlisError(f"Error generating report: {str(e)}")


def check_paid_user() -> bool:
    """Check if the current user is a paid user."""
    try:
        auth = get_sandstrike_auth()
        is_paid, subscription = auth.verify_api_key()
        
        if not is_paid or not subscription:
            console.print("[red][FAILED] Reports feature requires a Pro subscription[/red]")
            console.print("[yellow]Please verify your API key and upgrade to Pro to access HTML report generation[/yellow]")
            console.print("[dim]Run 'sandstrike auth verify' to check your subscription status[/dim]")
            return False
            
        if not subscription.is_paid_user:
            console.print("[red][FAILED] Reports feature requires a Pro subscription[/red]")
            console.print(f"[yellow]Current subscription: {subscription.subscription_type}[/yellow]")
            console.print("[yellow]Upgrade to Pro to access HTML report generation[/yellow]")
            console.print("[dim]Run 'sandstrike auth verify' to check your subscription status[/dim]")
            return False
            
        return True
    except Exception as e:
        console.print("[red][FAILED] Reports feature requires a Pro subscription[/red]")
        console.print("[yellow]Unable to verify subscription status[/yellow]")
        console.print("[dim]Run 'sandstrike auth verify' to check your subscription status[/dim]")
        return False


def get_sessions() -> list:
    """Get list of available sessions from the backend."""
    try:
        import requests
        import os
        
        # Try to get sessions from the local server
        base_url = os.getenv('AVENLIS_SERVER_URL', 'http://localhost:5000')
        
        try:
            response = requests.get(f"{base_url}/api/sessions", timeout=5)
            if response.status_code == 200:
                sessions_data = response.json()
                # Transform the data to match our expected format
                formatted_sessions = []
                for session in sessions_data:
                    # Calculate metrics from results
                    results = session.get('results', [])
                    total_prompts = len(results)
                    passed_prompts = len([r for r in results if r.get('status') == 'passed'])
                    failed_prompts = len([r for r in results if r.get('status') == 'failed'])
                    error_prompts = len([r for r in results if r.get('status') == 'error'])
                    
                    formatted_sessions.append({
                        "id": session.get('id'),
                        "name": session.get('session_name', session.get('name', 'Unknown')),
                        "session_name": session.get('session_name', session.get('name', 'Unknown')),
                        "status": session.get('status', 'unknown'),
                        "createdAt": session.get('started_at', session.get('created_at', '')),
                        "totalPrompts": total_prompts,
                        "passedPrompts": passed_prompts,
                        "failedPrompts": failed_prompts,
                        "errorPrompts": error_prompts,
                        "target": session.get('target', ''),
                        "targetModel": session.get('target_model', ''),
                        "vulnerabilitiesFound": session.get('vulnerabilities_found', failed_prompts),
                        "tags": session.get('tags', []),
                        "results": results  # Include the actual results array for metrics calculation
                    })
                return formatted_sessions
        except requests.exceptions.RequestException:
            pass
        
        # Fallback: try to read from local sessions.json file
        import json
        # Try multiple possible paths for sessions.json
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sessions.json'),
            os.path.join(os.getcwd(), 'avenlis', 'data', 'sessions.json'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sessions.json')
        ]
        
        for sessions_file in possible_paths:
            if os.path.exists(sessions_file):
                try:
                    with open(sessions_file, 'r') as f:
                        data = json.load(f)
                        sessions_data = data.get('scan_results', [])
                        formatted_sessions = []
                        for session in sessions_data:
                            results = session.get('results', [])
                            total_prompts = len(results)
                            passed_prompts = len([r for r in results if r.get('status') == 'passed'])
                            failed_prompts = len([r for r in results if r.get('status') == 'failed'])
                            error_prompts = len([r for r in results if r.get('status') == 'error'])
                            
                            formatted_sessions.append({
                                "id": session.get('id'),
                                "name": session.get('session_name', session.get('name', 'Unknown')),
                                "session_name": session.get('session_name', session.get('name', 'Unknown')),
                                "status": session.get('status', 'unknown'),
                                "createdAt": session.get('started_at', session.get('created_at', '')),
                                "totalPrompts": total_prompts,
                                "passedPrompts": passed_prompts,
                                "failedPrompts": failed_prompts,
                                "errorPrompts": error_prompts,
                                "target": session.get('target', ''),
                                "targetModel": session.get('target_model', ''),
                                "vulnerabilitiesFound": session.get('vulnerabilities_found', failed_prompts),
                                "tags": session.get('tags', []),
                                "results": results  # Include the actual results array for metrics calculation
                            })
                        return formatted_sessions
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not read {sessions_file}: {e}[/yellow]")
                    continue
        
        return []
        
    except Exception as e:
        console.print(f"[red]Error loading sessions:[/red] {e}")
        return []


@reports_group.command(name="overview")
@click.option("--session-id", "-s", help="Comma-separated list of session IDs (e.g., 'session1,session2,session3')")
@click.option("--source", type=click.Choice(['local', 'file', 'all']), default='all', help="Session source filter (default: all)")
@click.option("--output", "-o", help="Output file prefix name (e.g., 'testreport' creates 'testreport_overview.html')")
def generate_overview_report(session_id: str, source: str, output: str) -> None:
    """Generate an Overview HTML Report with high-level security metrics."""
    try:
        # Check if user is paid
        if not check_paid_user():
            return

        console.print("[blue]Generating Overview HTML Report...[/blue]")
        
        # Get sessions
        sessions = get_sessions()
        if not sessions:
            console.print("[red][FAILED] No sessions found[/red]")
            return

        # Handle session selection
        if session_id:
            # Use specific session IDs
            selected_session_ids = [s.strip() for s in session_id.split(',')]
            selected_sessions = [s for s in sessions if s['id'] in selected_session_ids]
        else:
            # Use all sessions based on source filter (default behavior)
            if source == 'all':
                selected_sessions = sessions
            elif source == 'local':
                selected_sessions = [s for s in sessions if s.get('source') == 'local']
            elif source == 'file':
                selected_sessions = [s for s in sessions if s.get('source') == 'file']
            else:
                selected_sessions = sessions
            
            console.print(f"[blue]Using all {len(selected_sessions)} sessions from {source} source[/blue]")

        if not selected_sessions:
            console.print("[red][FAILED] No valid sessions selected[/red]")
            return

        # Generate report
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Generating Overview HTML Report...", total=100)
            
            # Actually generate the HTML report
            progress.update(task, advance=25, description="Collecting session data...")
            
            # Generate HTML content
            html_content = generate_html_report(selected_sessions, 'overview')
            
            progress.update(task, advance=25, description="Analyzing security metrics...")
            progress.update(task, advance=25, description="Generating HTML...")
            progress.update(task, advance=25, description="Finalizing report...")

        # Get sandstrike package directory (go up from sandstrike/cli/commands/reports.py to sandstrike/)
        current_file = Path(__file__).resolve()
        sandstrike_dir = current_file.parent.parent.parent
        reports_dir = sandstrike_dir / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        if output:
            # Use provided prefix
            output_path = reports_dir / f"{output}_overview.html"
        else:
            # Default: use timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = reports_dir / f"overview_{timestamp}.html"
        
        output = str(output_path)

        console.print(f"\n[green][SUCCESS] Overview HTML Report generated successfully![/green]")
        console.print(f"[blue]Output file:[/blue] {output}")
        console.print(f"[blue]Sessions included:[/blue] {len(selected_sessions)}")
        
        # Save the HTML file
        try:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            console.print(f"[green]🌐 HTML report saved to: {output}[/green]")
            console.print(f"[blue]Open in browser:[/blue] file://{os.path.abspath(output)}")
        except Exception as e:
            console.print(f"[red]Error saving HTML report: {e}[/red]")
            return
        
        # Show summary
        total_prompts = sum(s['totalPrompts'] for s in selected_sessions)
        total_passed = sum(s['passedPrompts'] for s in selected_sessions)
        total_failed = sum(s['failedPrompts'] for s in selected_sessions)
        
        summary_panel = f"[bold]Report Summary[/bold]\n\n"
        summary_panel += f"Total Sessions: {len(selected_sessions)}\n"
        summary_panel += f"Total Prompts: {total_prompts}\n"
        summary_panel += f"Passed: {total_passed} ({total_passed/total_prompts*100:.1f}%)\n"
        summary_panel += f"Failed: {total_failed} ({total_failed/total_prompts*100:.1f}%)\n"
        
        console.print(Panel(summary_panel, title="Overview Report", border_style="green"))
        
    except Exception as e:
        console.print(f"[red]Error generating overview report:[/red] {e}")
        raise click.Abort()


@reports_group.command(name="detailed")
@click.option("--session-id", "-s", help="Comma-separated list of session IDs (e.g., 'session1,session2,session3')")
@click.option("--source", type=click.Choice(['local', 'file', 'all']), default='all', help="Session source filter (default: all)")
@click.option("--output", "-o", help="Output file prefix name (e.g., 'testreport' creates 'testreport_detailed.html')")
def generate_detailed_report(session_id: str, source: str, output: str) -> None:
    """Generate a Detailed HTML Report with comprehensive analysis including vulnerabilities and recommendations."""
    try:
        # Check if user is paid
        if not check_paid_user():
            return

        console.print("[blue]Generating Detailed HTML Report...[/blue]")
        
        # Get sessions
        sessions = get_sessions()
        if not sessions:
            console.print("[red][FAILED] No sessions found[/red]")
            return

        # Handle session selection
        if session_id:
            # Use specific session IDs
            selected_session_ids = [s.strip() for s in session_id.split(',')]
            selected_sessions = [s for s in sessions if s['id'] in selected_session_ids]
        else:
            # Use all sessions based on source filter (default behavior)
            if source == 'all':
                selected_sessions = sessions
            elif source == 'local':
                selected_sessions = [s for s in sessions if s.get('source') == 'local']
            elif source == 'file':
                selected_sessions = [s for s in sessions if s.get('source') == 'file']
            else:
                selected_sessions = sessions
            
            console.print(f"[blue]Using all {len(selected_sessions)} sessions from {source} source[/blue]")

        if not selected_sessions:
            console.print("[red][FAILED] No valid sessions selected[/red]")
            return

        # Generate report
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Generating Detailed HTML Report...", total=100)
            
            # Actually generate the HTML report
            progress.update(task, advance=20, description="Collecting session data...")
            
            # Generate HTML content
            html_content = generate_html_report(selected_sessions, 'detailed')
            
            progress.update(task, advance=20, description="Analyzing vulnerabilities...")
            progress.update(task, advance=20, description="Generating recommendations...")
            progress.update(task, advance=20, description="Creating detailed analysis...")
            progress.update(task, advance=20, description="Generating HTML...")

        # Get sandstrike package directory (go up from sandstrike/cli/commands/reports.py to sandstrike/)
        current_file = Path(__file__).resolve()
        sandstrike_dir = current_file.parent.parent.parent
        reports_dir = sandstrike_dir / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        if output:
            # Use provided prefix
            output_path = reports_dir / f"{output}_detailed.html"
        else:
            # Default: use timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = reports_dir / f"detailed_{timestamp}.html"
        
        output = str(output_path)

        console.print(f"\n[green][SUCCESS] Detailed HTML Report generated successfully![/green]")
        console.print(f"[blue]Output file:[/blue] {output}")
        console.print(f"[blue]Sessions included:[/blue] {len(selected_sessions)}")
        
        # Save the HTML file
        try:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            console.print(f"[green]🌐 HTML report saved to: {output}[/green]")
            console.print(f"[blue]Open in browser:[/blue] file://{os.path.abspath(output)}")
        except Exception as e:
            console.print(f"[red]Error saving HTML report: {e}[/red]")
            return
        
    except Exception as e:
        console.print(f"[red]Error generating detailed report:[/red] {e}")
        raise click.Abort()


@reports_group.command(name="executive")
@click.option("--session-id", "-s", help="Comma-separated list of session IDs (e.g., 'session1,session2,session3')")
@click.option("--source", type=click.Choice(['local', 'file', 'all']), default='all', help="Session source filter (default: all)")
@click.option("--output", "-o", help="Output file prefix name (e.g., 'testreport' creates 'testreport_executive.html')")
def generate_executive_report(session_id: str, source: str, output: str) -> None:
    """Generate an Executive Summary HTML Report for leadership."""
    try:
        # Check if user is paid
        if not check_paid_user():
            return

        console.print("[blue]Generating Executive Summary HTML Report...[/blue]")
        
        # Get sessions
        sessions = get_sessions()
        if not sessions:
            console.print("[red][FAILED] No sessions found[/red]")
            return

        # Handle session selection
        if session_id:
            # Use specific session IDs
            selected_session_ids = [s.strip() for s in session_id.split(',')]
            selected_sessions = [s for s in sessions if s['id'] in selected_session_ids]
        else:
            # Use all sessions based on source filter (default behavior)
            if source == 'all':
                selected_sessions = sessions
            elif source == 'local':
                selected_sessions = [s for s in sessions if s.get('source') == 'local']
            elif source == 'file':
                selected_sessions = [s for s in sessions if s.get('source') == 'file']
            else:
                selected_sessions = sessions
            
            console.print(f"[blue]Using all {len(selected_sessions)} sessions from {source} source[/blue]")

        if not selected_sessions:
            console.print("[red][FAILED] No valid sessions selected[/red]")
            return

        # Generate report
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Generating Executive Summary HTML Report...", total=100)
            
            # Actually generate the HTML report
            progress.update(task, advance=25, description="Analyzing security posture...")
            
            # Generate HTML content
            html_content = generate_html_report(selected_sessions, 'executive')
            
            progress.update(task, advance=25, description="Calculating risk metrics...")
            progress.update(task, advance=25, description="Preparing executive summary...")
            progress.update(task, advance=25, description="Generating HTML...")

        # Get sandstrike package directory (go up from sandstrike/cli/commands/reports.py to sandstrike/)
        current_file = Path(__file__).resolve()
        sandstrike_dir = current_file.parent.parent.parent
        reports_dir = sandstrike_dir / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        if output:
            # Use provided prefix
            output_path = reports_dir / f"{output}_executive.html"
        else:
            # Default: use timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = reports_dir / f"executive_{timestamp}.html"
        
        output = str(output_path)

        console.print(f"\n[green][SUCCESS] Executive Summary HTML Report generated successfully![/green]")
        console.print(f"[blue]Output file:[/blue] {output}")
        console.print(f"[blue]Sessions included:[/blue] {len(selected_sessions)}")
        
        # Save the HTML file
        try:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            console.print(f"[green]🌐 HTML report saved to: {output}[/green]")
            console.print(f"[blue]Open in browser:[/blue] file://{os.path.abspath(output)}")
        except Exception as e:
            console.print(f"[red]Error saving HTML report: {e}[/red]")
            return
        
        # Show executive summary
        total_prompts = sum(s['totalPrompts'] for s in selected_sessions)
        total_failed = sum(s['failedPrompts'] for s in selected_sessions)
        risk_score = (total_failed / total_prompts) * 100 if total_prompts > 0 else 0
        
        summary_panel = f"[bold]Executive Summary[/bold]\n\n"
        summary_panel += f"Security Risk Score: {risk_score:.1f}%\n"
        summary_panel += f"Total Tests Conducted: {total_prompts}\n"
        summary_panel += f"Critical Issues Found: {total_failed}\n"
        summary_panel += f"Assessment Period: {len(selected_sessions)} sessions\n\n"
        
        if risk_score < 10:
            summary_panel += "[green][OK] Security posture is strong[/green]\n"
        elif risk_score < 25:
            summary_panel += "[yellow][WARNING] Security posture needs attention[/yellow]\n"
        else:
            summary_panel += "[red][WARNING] Security posture requires immediate action[/red]\n"
        
        console.print(Panel(summary_panel, title="Executive Summary", border_style="blue"))
        
    except Exception as e:
        console.print(f"[red]Error generating executive report:[/red] {e}")
        raise click.Abort()


def get_sessions_data(session_id, source):
    """Get sessions data based on session IDs and source."""
    try:
        import requests
        import os
        import json
        
        # Try to get sessions from the local server
        base_url = os.getenv('AVENLIS_SERVER_URL', 'http://localhost:5000')
        
        try:
            response = requests.get(f"{base_url}/api/sessions", timeout=5)
            if response.status_code == 200:
                sessions_data = response.json()
                # Filter by session IDs if provided
                if session_id:
                    session_id_list = [s.strip() for s in session_id.split(',')]
                    sessions_data = [s for s in sessions_data if s.get('id') in session_id_list]
                return sessions_data
        except requests.exceptions.RequestException:
            pass
        
        # Fallback: try to read from local sessions.json file
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sessions.json'),
            os.path.join(os.getcwd(), 'avenlis', 'data', 'sessions.json'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sessions.json')
        ]
        
        for sessions_file in possible_paths:
            if os.path.exists(sessions_file):
                with open(sessions_file, 'r') as f:
                    data = json.load(f)
                    sessions_data = data.get('scan_results', [])
                    # Filter by session IDs if provided
                    if session_id:
                        session_id_list = [s.strip() for s in session_id.split(',')]
                        sessions_data = [s for s in sessions_data if s.get('id') in session_id_list]
                    return sessions_data
        
        return []
        
    except Exception as e:
        console.print(f"[red]Error getting sessions data:[/red] {e}")
        return []


def get_sample_sessions_data():
    """Get sample sessions data for testing."""
    try:
        import json
        import os
        
        # Try to read from local sessions.json file
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sessions.json'),
            os.path.join(os.getcwd(), 'avenlis', 'data', 'sessions.json'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sessions.json')
        ]
        
        for sessions_file in possible_paths:
            if os.path.exists(sessions_file):
                with open(sessions_file, 'r') as f:
                    data = json.load(f)
                    return data.get('scan_results', [])[:2]  # Return first 2 sessions for testing
        
        return []
        
    except Exception as e:
        console.print(f"[red]Error getting sample sessions data:[/red] {e}")
        return []


@reports_group.command(name="all")
@click.option("--session-id", "-s", help="Comma-separated list of session IDs (e.g., 'session1,session2,session3')")
@click.option("--source", "-src", type=click.Choice(['local', 'file', 'all']), default='all', help="Data source to use (default: all)")
@click.option("--output", "-o", help="Output file prefix name (e.g., 'testreport' creates 'testreport_overview.html', 'testreport_detailed.html', 'testreport_executive.html')")
def generate_all_reports(session_id, source, output):
    """Generate all three report types (overview, detailed, executive) at once."""
    
    # Check if user is paid
    check_paid_user()
    
    try:
        # Get sessions data based on parameters
        sessions_data = get_sessions_data(session_id, source)
        
        if not sessions_data:
            console.print("[red]No sessions found matching the criteria.[/red]")
            return
        
        # Get sandstrike package directory (go up from sandstrike/cli/commands/reports.py to sandstrike/)
        current_file = Path(__file__).resolve()
        sandstrike_dir = current_file.parent.parent.parent
        output_dir = sandstrike_dir / 'reports'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for consistent naming (used if no prefix provided)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate all three reports
        report_types = ['overview', 'detailed', 'executive']
        generated_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            for report_type in report_types:
                task = progress.add_task(f"Generating {report_type} report...", total=100)
                
                try:
                    # Generate HTML content
                    html_content = generate_html_report(sessions_data, report_type)
                    
                    # Determine filename
                    if output:
                        # Use provided prefix
                        filename = f"{output}_{report_type}.html"
                    else:
                        # Default: use timestamp
                        filename = f"{report_type}_{timestamp}.html"
                    
                    output_path = output_dir / filename
                    
                    # Save HTML file
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    generated_files.append(str(output_path))
                    progress.update(task, advance=100)
                    
                except Exception as e:
                    console.print(f"[red]Error generating {report_type} report:[/red] {e}")
                    progress.update(task, advance=100)
                    continue
        
        # Display success message
        console.print(f"\n[green][OK] Successfully generated all reports![/green]")
        console.print(f"[blue]Generated {len(generated_files)} report(s):[/blue]")
        
        for file_path in generated_files:
            console.print(f"  • {file_path}")
        
        console.print(f"\n[blue]Reports saved to:[/blue] {output_dir}")
        console.print("[yellow]Open the HTML files in your browser to view the reports.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error generating all reports:[/red] {e}")
        raise click.Abort()

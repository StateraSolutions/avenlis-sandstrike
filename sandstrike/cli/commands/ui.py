"""
UI command for starting the SandStrike web interface.

This module provides commands to start both the Python backend server and React frontend,
providing a unified development experience.
"""

import os
import sys
import time
import socket
import webbrowser
import subprocess
import threading
from threading import Timer
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table

from sandstrike.config import AvenlisConfig
from sandstrike.server import AvenlisServer
from sandstrike.exceptions import AvenlisError

console = Console()


@click.group(name="ui")
def ui_group():
    """Starting and managing the SandStrike web interface."""
    pass


@ui_group.command()
@click.pass_context
def start(ctx: click.Context) -> None:
    """
    Start the SandStrike web interface with both backend and React frontend.
    
    This starts:
    - Python Flask backend server (API + Socket.IO) on port 8080 using LOCAL development code
    - React development server (with hot reload) on port 3000 in separate terminal
    - Automatically opens the React UI in your browser
    
    Both servers run in separate processes/terminals to avoid WebSocket conflicts.
    
    Note: Uses local development code, not the installed package version.
    
    Example:
        sandstrike ui start
    """
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        web_ui_dir = os.path.join(project_root, "sandstrike", "web-ui")
        
        # Check if web-ui directory exists
        if not os.path.exists(web_ui_dir):
            console.print(f"[red]Error: React frontend directory not found at {web_ui_dir}[/red]")
            console.print("Make sure you're running this from the correct directory.")
            sys.exit(1)
        
        # Check if package.json exists
        package_json = os.path.join(web_ui_dir, "package.json")
        if not os.path.exists(package_json):
            console.print(f"[red]Error: package.json not found at {package_json}[/red]")
            console.print("Make sure the React frontend is properly set up.")
            sys.exit(1)
        
        # Display startup info
        backend_url = "http://127.0.0.1:8080"
        frontend_url = "http://127.0.0.1:3000"
        
        console.print(
            Panel(
                f" Starting SandStrike Full Stack...\n\n"
                f"[bold]Backend URL:[/bold] {backend_url}\n"
                f"[bold]Frontend URL:[/bold] {frontend_url}\n"
                f"[dim]Press Ctrl+C to stop all servers[/dim]",
                title="SandStrike Web Interface",
                border_style="blue"
            )
        )
        
        # Start backend server in the main terminal (show logs)
        def start_backend():
            try:
                # Use local development code instead of installed package
                # Get the sandstrike directory (parent of cli/commands)
                sandstrike_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                console.print(f"[dim]Using local development code from: {sandstrike_dir}[/dim]")
                
                # Use subprocess to start the backend server in the main terminal
                backend_process = subprocess.Popen(
                    ["python", "-m", "sandstrike.server", "--host", "127.0.0.1", "--port", "8080"],
                    cwd=sandstrike_dir,  # Use local sandstrike directory
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                return backend_process
            except Exception as e:
                console.print(f"[red]Backend error: {e}[/red]")
                return None
        
        backend_process = start_backend()
        
        if not backend_process:
            console.print("[red]Failed to start backend server[/red]")
            sys.exit(1)
        
        # Check if backend process is still running after a moment
        time.sleep(1)
        if backend_process.poll() is not None:
            console.print("[red]Backend server exited immediately. Check for errors above.[/red]")
            sys.exit(1)
        
        # Start a thread to display backend logs
        def display_backend_logs():
            if backend_process and backend_process.stdout:
                for line in iter(backend_process.stdout.readline, ''):
                    if line:
                        console.print(f"[dim]{line.strip()}[/dim]")
        
        backend_log_thread = threading.Thread(target=display_backend_logs, daemon=True)
        backend_log_thread.start()
        
        # Wait for backend to be ready
        console.print("[yellow]Waiting for backend server to start...[/yellow]")
        backend_ready = False
        for i in range(30):  # Wait up to 30 seconds
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', 8080))
                sock.close()
                if result == 0:
                    backend_ready = True
                    console.print("[green][OK] Backend server is ready[/green]")
                    break
            except:
                pass
            time.sleep(1)
        
        if not backend_ready:
            console.print("[red]Backend server did not start on port 8080[/red]")
            console.print("[yellow]Check if port 8080 is already in use or if there are errors above[/yellow]")
            if backend_process:
                backend_process.terminate()
            sys.exit(1)
        
        # Start React development server with visible output
        def start_frontend():
            try:
                # Set environment variables for React
                env = os.environ.copy()
                env['VITE_BACKEND_URL'] = backend_url
                
                # Check if node_modules exists
                node_modules = os.path.join(web_ui_dir, "node_modules")
                if not os.path.exists(node_modules):
                    console.print("[yellow][WARNING]  node_modules not found. Installing dependencies...[/yellow]")
                    console.print("[dim]This may take a few minutes on first run[/dim]")
                    install_process = subprocess.Popen(
                        "npm install",
                        cwd=web_ui_dir,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    for line in iter(install_process.stdout.readline, ''):
                        if line:
                            console.print(f"[dim]{line.strip()}[/dim]")
                    install_process.wait()
                    if install_process.returncode != 0:
                        console.print("[red]Failed to install npm dependencies[/red]")
                        return None
                
                # Use subprocess.Popen to start frontend (show output for debugging)
                frontend_process = subprocess.Popen(
                    "npm run dev -- --port 3000 --host 127.0.0.1",
                    cwd=web_ui_dir,
                    env=env,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                return frontend_process
            except Exception as e:
                console.print(f"[red]Frontend error: {e}[/red]")
                return None
        
        frontend_process = start_frontend()
        
        if not frontend_process:
            console.print("[red]Failed to start frontend server[/red]")
            if backend_process:
                backend_process.terminate()
            sys.exit(1)
        
        # Start a thread to display frontend logs
        def display_frontend_logs():
            if frontend_process and frontend_process.stdout:
                for line in iter(frontend_process.stdout.readline, ''):
                    if line:
                        console.print(f"[cyan][frontend] {line.strip()}[/cyan]")
        
        frontend_log_thread = threading.Thread(target=display_frontend_logs, daemon=True)
        frontend_log_thread.start()
        
        # Wait for frontend to be ready
        console.print("[yellow]Waiting for frontend server to start...[/yellow]")
        frontend_ready = False
        for i in range(30):  # Wait up to 30 seconds
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', 3000))
                sock.close()
                if result == 0:
                    frontend_ready = True
                    console.print("[green][OK] Frontend server is ready[/green]")
                    break
            except:
                pass
            time.sleep(1)
        
        if not frontend_ready:
            console.print("[red]Frontend server did not start on port 3000[/red]")
            console.print("[yellow]Check if port 3000 is already in use or if there are errors above[/yellow]")
            if frontend_process:
                frontend_process.terminate()
            if backend_process:
                backend_process.terminate()
            sys.exit(1)
        
        # Additional wait to ensure everything is fully ready
        time.sleep(2)
        
        # Auto-open browser
        def open_browser():
            try:
                webbrowser.open(frontend_url)
                console.print(f"[green][OK][/green] Opened browser at {frontend_url}")
            except Exception:
                console.print(f"[yellow][WARNING][/yellow] Could not open browser. Visit {frontend_url} manually.")
        
        Timer(2, open_browser).start()
        
        # Display status
        console.print(
            Panel(
                f"[SUCCESS] [bold green]Both servers started successfully![/bold green]\n\n"
                f"[bold]Backend:[/bold] {backend_url}\n"
                f"[bold]Frontend:[/bold] {frontend_url}\n\n"
                f"[dim]Press Ctrl+C to stop all servers[/dim]",
                title="Server Status",
                border_style="green"
            )
        )
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping all servers...[/yellow]")
            if backend_process:
                backend_process.terminate()
                backend_process.wait()
            if frontend_process:
                frontend_process.terminate()
                frontend_process.wait()
            console.print("[green][OK][/green] All servers stopped")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Servers stopped by user[/yellow]")
    except AvenlisError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)




"""
Grader command for SandStrike CLI.

This module provides the grader command for grading responses using the production LLM chatbot
at avenlis.staterasolv.com.
"""

import os
import json
import click
import requests
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from sandstrike.sandstrike_auth import get_sandstrike_auth, load_env_file
from sandstrike.exceptions import AvenlisError

console = Console()
load_env_file()

def call_grader_api(input_text: str, output_text: str, api_key: str, grader_intent: str) -> dict:
    """Call the grader API endpoint."""
    url = "https://avenlis.staterasolv.com/llm/grade-response"
    
    payload = {
        "api_key": api_key,
        "input_text": input_text,
        "output_text": output_text,
        "grader_intent": grader_intent
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise AvenlisError("Invalid API key")
        elif response.status_code == 403:
            raise AvenlisError("Grading features require Pro subscription")
        elif response.status_code == 400:
            error_data = response.json()
            raise AvenlisError(f"Bad request: {error_data.get('error', 'Unknown error')}")
        else:
            error_data = response.json()
            raise AvenlisError(f"API error: {error_data.get('error', 'Unknown error')}")
            
    except requests.exceptions.Timeout:
        raise AvenlisError("Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise AvenlisError("Could not connect to grading service. Please check your internet connection.")
    except requests.exceptions.RequestException as e:
        raise AvenlisError(f"Request failed: {str(e)}")

def display_grading_result(result: dict) -> None:
    """Display the grading result in a formatted table."""
    grading_result = result.get("grading_result", {})
    
    # Extract simplified fields
    grade = grading_result.get("grade", "UNKNOWN")
    confidence = grading_result.get("confidence", 0.0)
    reasoning = grading_result.get("reasoning", "No reasoning provided")
    grader_intent = grading_result.get("grader_intent", "No intent specified")
    
    # Color coding for grade
    if grade == "PASS":
        grade_color = "green"
        grade_icon = "[SUCCESS]"
    elif grade == "FAIL":
        grade_color = "red"
        grade_icon = "[FAILED]"
    else:
        grade_color = "yellow"
        grade_icon = "[WARNING]"
    
    # Color coding for confidence
    if confidence == "High":
        confidence_color = "green"
    elif confidence == "Medium":
        confidence_color = "yellow"
    elif confidence == "Low":
        confidence_color = "red"
    else:
        confidence_color = "white"
    
    # Create a table for the results
    table = Table(title="Grading Results", show_header=True, header_style="bold blue")
    table.add_column("Grade", style="cyan", width=20)
    table.add_column("Confidence", style="yellow", width=15)
    table.add_column("Reasoning", style="white", width=50)
    table.add_column("Grader Intent", style="magenta", width=30)
    
    # Add single row with all values
    table.add_row(
        f"{grade_icon} [{grade_color}]{grade}[/{grade_color}]",
        f"[{confidence_color}]{confidence}[/{confidence_color}]",
        reasoning,
        grader_intent
    )
    
    console.print(table)
    
    # Print raw JSON response
    console.print("\n[bold blue]Raw JSON Response:[/bold blue]")
    console.print(f"[dim]{json.dumps(grading_result, indent=2)}[/dim]")

@click.command(name="grader")
@click.option("--input", "-i", required=True, help="Input prompt text")
@click.option("--output", "-o", required=True, help="Output response text to grade")
@click.option("--intent", "-t", required=True, help="Grading intent/criteria (required)")
@click.option("--api-key", help="API key (if not set in environment)")
def grader(input: str, output: str, intent: str, api_key: Optional[str]) -> None:
    """Grade a response using the production LLM chatbot (Pro users only)."""
    try:
        # Get API key
        if not api_key:
            api_key = os.getenv('AVENLIS_API_KEY')
            if not api_key:
                console.print("[red]No API key found[/red]")
                console.print("[yellow]Please set AVENLIS_API_KEY environment variable or use --api-key[/yellow]")
                return
        
        api_key = api_key.strip()
        
        console.print("[blue]🔍 Grading response...[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Sending request to grading service...", total=None)
            
            result = call_grader_api(input, output, api_key, intent)
            
            progress.update(task, description="[SUCCESS] Grading completed")
        
        # Display the result
        display_grading_result(result)
        
    except AvenlisError as e:
        console.print(f"[red]Error:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")

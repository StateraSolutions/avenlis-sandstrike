"""
Main CLI entry point for SandStrike.

This module provides the main command-line interface for the SandStrike library.
"""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.traceback import install

from sandstrike import __version__
from sandstrike.cli.commands import ui, collections, prompts, sessions, auth, reports, database, variables, targets
from sandstrike.cli.commands.grader import grader
from sandstrike.utils.logging import setup_logging

# Install rich traceback handler for better error display
install(show_locals=True)

# Initialize rich console
console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="sandstrike", message="%(prog)s v%(version)s")
@click.option(
    "--config", "-c",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[str]) -> None:
    """
    SandStrike - AI Security Testing Framework
    
    A powerful command-line tool for red team testing of Large Language Models.
    Test your AI systems against adversarial prompts and security vulnerabilities.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Set up logging with default INFO level
    setup_logging(level="INFO")
    
    # Store configuration in context
    ctx.obj["config"] = config


# Add command groups
cli.add_command(ui.ui_group)
cli.add_command(collections.collections_group)
cli.add_command(targets.targets_group)
cli.add_command(auth.auth_group)
cli.add_command(reports.reports_group)
cli.add_command(database.database_group)
cli.add_command(variables.variables_group)

# Add new comprehensive commands matching React UI
cli.add_command(prompts.prompts_group)
cli.add_command(sessions.sessions_group)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

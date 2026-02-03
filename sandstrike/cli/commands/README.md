# CLI Commands

This directory contains the implementation of all SandStrike CLI commands, organized by functionality.

## 📋 **Available Commands**

### **🔐 Authentication (`auth.py`)**
- **`auth verify`**: Verify API key and check subscription status

### **📝 Prompts Management (`prompts.py`)**
- **`prompts list`**: List all adversarial prompts
- **`prompts view`**: Display detailed prompt information
- **`prompts create`**: Create new adversarial prompt
- **`prompts delete`**: Delete adversarial prompt

### **📊 Sessions Management (`sessions.py`)**
- **`sessions list`**: List all test sessions
- **`sessions show`**: Show detailed session information with security analysis

### **📁 Collections (`collections.py`)**
- **`collections create`**: Create new prompt collection
- **`collections list`**: List all collections
- **`collections add-prompt`**: Add prompt(s) to a collection
- **`collections remove-prompt`**: Remove a prompt from a collection
- **`collections delete`**: Delete collections and prompts

### **🎯 Targets (`targets.py`)**
- **`targets create`**: Create new scan target
- **`targets list`**: List all targets
- **`targets view`**: View detailed target information
- **`targets delete`**: Delete a target

### **📊 Reports (`reports.py`)**
- **`reports overview`**: Generate overview HTML report
- **`reports detailed`**: Generate detailed HTML report
- **`reports executive`**: Generate executive summary HTML report
- **`reports all`**: Generate all report types at once

### **🗄️ Database Management (`database.py`)**
- **`database status`**: Show database status and table information
- **`database local-wipe`**: Reset local SQLite to original tables

### **🔤 Dynamic Variables (`variables.py`)**
- **`variables list`**: List all dynamic variables
- **`variables set`**: Set a dynamic variable
- **`variables get`**: Get variables by category
- **`variables update`**: Update an existing variable

### **🖥️ Web Interface (`ui.py`)**
- **`ui start`**: Launch web interface (backend + frontend)

## 🛠️ Command Implementation Patterns

### Standard Command Structure
```python
import click
from rich.console import Console
from avenlis.exceptions import AvenlisError

console = Console()

@click.group(name="category")
def category_group():
    """Category description for help."""
    pass

@category_group.command()
@click.option('--option', '-o', help='Option description')
@click.argument('argument', required=False)
@click.pass_context
def command_name(ctx: click.Context, option: str, argument: str):
    """
    Command description.
    
    ARGUMENT description if needed.
    """
    try:
        # Get global options from context
        verbose = ctx.obj.get("verbose", False)
        
        if verbose:
            console.print(f"[dim]Processing: {argument}[/dim]")
        
        # Command implementation
        result = perform_action(argument, option)
        
        # Success output
        console.print("[green]✓[/green] Command completed")
        
    except AvenlisError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise click.Abort()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        raise click.Abort()
```

### Error Handling Pattern
```python
try:
    # Command logic
    result = risky_operation()
    
except AvenlisAuthError:
    console.print("[red]Authentication failed. Please run 'sandstrike auth login'[/red]")
    raise click.Abort()
    
except AvenlisNetworkError as e:
    console.print(f"[red]Network error: {e}[/red]")
    console.print("[yellow]Check your connection and try again[/yellow]")
    raise click.Abort()
    
except Exception as e:
    if ctx.obj.get("verbose"):
        console.print_exception()  # Full traceback in verbose mode
    else:
        console.print(f"[red]Unexpected error: {e}[/red]")
    raise click.Abort()
```

### Progress Display Pattern
```python
from rich.progress import Progress, SpinnerColumn, TextColumn

def long_running_command():
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Processing...", total=None)
        
        # Long running operation
        result = perform_operation()
        
        progress.update(task, description="✓ Complete")
```

### Confirmation Prompts
```python
if not click.confirm(f"Delete session '{session_name}'? This cannot be undone."):
    console.print("[yellow]Operation cancelled[/yellow]")
    return

# Proceed with destructive operation
```

## 🧪 Testing Commands

### Unit Tests
Each command module should have corresponding tests:

```python
# tests/test_cli_auth.py
from click.testing import CliRunner
from avenlis.cli.commands.auth import auth_group

def test_auth_login_success():
    runner = CliRunner()
    result = runner.invoke(auth_group, ['login'])
    assert result.exit_code == 0
    assert "Login successful" in result.output

def test_auth_whoami_not_authenticated():
    runner = CliRunner()
    result = runner.invoke(auth_group, ['whoami'])
    assert result.exit_code == 1
    assert "Not authenticated" in result.output
```

### Integration Tests
Test commands with real services (using test environment):

```python
@pytest.mark.integration
def test_prompts_list_integration():
    runner = CliRunner()
    result = runner.invoke(prompts_group, ['list'])
    assert result.exit_code == 0
    assert "Total prompts" in result.output
```

## 🎨 Output Styling Guidelines

### Success Messages
```python
console.print("[green]✓[/green] Operation completed successfully")
```

### Error Messages
```python
console.print("[red]✗[/red] Operation failed")
```

### Warning Messages
```python
console.print("[yellow]⚠️[/yellow] Warning: This is potentially dangerous")
```

### Info Messages
```python
console.print("[blue]ℹ️[/blue] Useful information")
```

### Progress/Debug
```python
if verbose:
    console.print(f"[dim]Debug: Processing {item}[/dim]")
```

## 📊 Command Output Formats

### Tables
```python
from rich.table import Table

table = Table(title="Attack Results")
table.add_column("Attack", style="cyan")
table.add_column("Status", style="green") 
table.add_column("Score", justify="right")

for result in results:
    status = "✓ Passed" if result.passed else "✗ Failed"
    table.add_row(result.name, status, f"{result.score:.1f}")

console.print(table)
```

### Panels
```python
from rich.panel import Panel

console.print(
    Panel(
        session_details,
        title=f"Session: {session.name}",
        border_style="blue"
    )
)
```

### JSON Output
```python
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def command(output_json):
    result = get_data()
    
    if output_json:
        click.echo(json.dumps(result, indent=2))
    else:
        # Rich formatted output
        display_formatted(result)
```

## 🤝 Adding New Commands

1. **Create the command module** in this directory
2. **Follow naming conventions**: `category.py` for command groups
3. **Import in `__init__.py`** if needed
4. **Register in `../main.py`**:
   ```python
   from avenlis.cli.commands import newcategory
   cli.add_command(newcategory.newcategory_group)
   ```
5. **Add comprehensive tests**
6. **Update this README**

## 🔧 Command Configuration

Commands can access configuration through:

```python
from avenlis.config import AvenlisConfig

@click.command()
@click.pass_context
def command(ctx):
    config = AvenlisConfig()
    
    # Environment variables
    api_host = config.get('AVENLIS_API_HOST')
    
    # Global CLI options
    verbose = ctx.obj.get('verbose', False)
    config_file = ctx.obj.get('config')
```

## 📚 Dependencies

- **Click**: Command-line interface framework
- **Rich**: Terminal formatting and styling
- **Avenlis Core**: Main package components

## 🎯 Best Practices

1. **Consistent help text**: Clear descriptions and examples
2. **Progressive disclosure**: Simple commands with advanced options
3. **Graceful error handling**: Meaningful error messages
4. **User confirmation**: Prompt for destructive operations
5. **Progress feedback**: Show progress for long operations
6. **Consistent styling**: Use established Rich styling patterns

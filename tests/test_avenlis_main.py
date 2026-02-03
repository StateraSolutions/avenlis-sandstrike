from click.testing import CliRunner
from sandstrike.cli.main import cli  # Adjust import if your CLI entry point is elsewhere

import webbrowser




def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]" in result.output # Check the first part of the

def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert "sandstrike v" in result.output

def test_auth_verify():
    runner = CliRunner()
    result = runner.invoke(cli, ['auth', 'verify'])
    assert result.exit_code == 0
    assert "You have access to all SandStrike premium features!" in result.output or "Invalid API key or verification failed" in result.output.lower()

def test_db_status():
    runner = CliRunner()
    result = runner.invoke(cli, ['database', 'status'])
    assert result.exit_code == 0
    assert "Database is clean - no redundant tables found!" in result.output

def test_db_wipe():
    runner = CliRunner()
    result = runner.invoke(cli, ['database', 'local-wipe'], input="y\n")
    assert result.exit_code == 0
    assert "Database functionality verified!" in result.output
    assert "Database cleanup completed!" in result.output

# def test_ui_start(monkeypatch):
#     opened_urls = []
#     # Fake browser open
#     def fake_open(url, *args, **kwargs):
#         opened_urls.append(url)
#         return True
    
#     monkeypatch.setattr(webbrowser, "open", fake_open)
    
#     runner = CliRunner()
#     result = runner.invoke(cli, ['ui', 'start'])
#     assert result.exit_code == 0
#     assert "Both servers started successfully! " in result.output or "Opened browser at http://127.0.0.1:3000" in result.output
#     assert opened_urls == ["http://127.0.0.1:3000"]
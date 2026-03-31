from click.testing import CliRunner
from sandstrike.cli.main import cli

def test_reports_overview():
    runner = CliRunner()
    result = runner.invoke(cli, ["reports", "overview"])
    assert result.exit_code == 0
    assert "Using all" in result.output
    assert "Overview HTML Report generated successfully!" in result.output

def test_reports_overview_with_session_id():
    runner = CliRunner()
    session_id = "sample_scan_001"
    result = runner.invoke(cli, [
        "reports", "overview",
        "--session-id", session_id
    ])
    assert result.exit_code == 0
    assert "Overview HTML Report generated successfully!" in result.output

def test_reports_overview_with_session_ids():
    runner = CliRunner()
    session_id1 = "sample_scan_001"
    session_id2 = "scan_9_1757665129"

    result = runner.invoke(cli, [
        "reports", "overview",
        "--session-id", f"{session_id1}, {session_id2}"
    ])
    assert result.exit_code == 0
    assert "Overview HTML Report generated successfully!" in result.output

def test_reports_overview_with_invalid_session_id():
    runner = CliRunner()
    session_id = "non_existent_session"
    result = runner.invoke(cli, [
        "reports", "overview",
        "--session-id", session_id
    ])
    assert result.exit_code == 0
    assert "❌ No valid sessions selected" in result.output

def test_reports_detailed():
    runner = CliRunner()
    result = runner.invoke(cli, ["reports", "detailed"])
    assert result.exit_code == 0
    assert "Using all" in result.output
    assert "Detailed HTML Report generated successfully!" in result.output

def test_reports_detailed_with_session_id():
    runner = CliRunner()
    session_id = "sample_scan_001"
    result = runner.invoke(cli, [
        "reports", "detailed",
        "--session-id", session_id
    ])
    assert result.exit_code == 0
    assert 'Detailed HTML Report generated successfully' in result.output

def test_reports_detailed_with_session_ids():
    runner = CliRunner()
    session_id1 = "sample_scan_001"
    session_id2 = "scan_9_1757665129"

    result = runner.invoke(cli, [
        "reports", "detailed",
        "--session-id", f"{session_id1}, {session_id2}"
    ])
    assert result.exit_code == 0
    assert 'Detailed HTML Report generated successfully' in result.output

def test_reports_detailed_with_invalid_session_id():
    runner = CliRunner()
    session_id = "non_existent_session"
    result = runner.invoke(cli, [
        "reports", "detailed",
        "--session-id", session_id
    ])
    assert result.exit_code == 0
    assert "❌ No valid sessions selected" in result.output

def test_reports_executive():
    runner = CliRunner()
    result = runner.invoke(cli, ["reports", "executive"])
    assert result.exit_code == 0
    assert "Using all" in result.output
    assert "Executive Summary HTML Report generated successfully!" in result.output

def test_reports_executive_with_session_id():
    runner = CliRunner()
    session_id = "sample_scan_001"
    result = runner.invoke(cli, [
        "reports", "executive",
        "--session-id", session_id
    ])
    assert result.exit_code == 0
    assert "Executive Summary HTML Report generated successfully" in result.output

def test_reports_executive_with_session_ids():
    runner = CliRunner()
    session_id1 = "sample_scan_001"
    session_id2 = "scan_9_1757665129"

    result = runner.invoke(cli, [
        "reports", "executive",
        "--session-id", f"{session_id1}, {session_id2}"
    ])
    assert result.exit_code == 0
    assert "Executive Summary HTML Report generated successfully" in result.output

def test_reports_executive_with_invalid_session_id():
    runner = CliRunner()
    session_id = "non_existent_session"
    result = runner.invoke(cli, [
        "reports", "executive",
        "--session-id", session_id
    ])
    assert result.exit_code == 0
    assert "❌ No valid sessions selected" in result.output

def test_reports_all():
    runner = CliRunner()
    result = runner.invoke(cli, ["reports", "all"])
    assert result.exit_code == 0
    assert "Generated 3 report" in result.output
    assert "✓ Successfully generated all reports!" in result.output

def test_reports_all_with_session_id():
    runner = CliRunner()
    session_id = "sample_scan_001"
    result = runner.invoke(cli, [
        "reports", "all",
        "--session-id", session_id
    ])
    assert result.exit_code == 0
    assert "Generated 3 report" in result.output
    assert "✓ Successfully generated all reports!" in result.output

def test_reports_all_with_session_ids():
    runner = CliRunner()
    session_id1 = "sample_scan_001"
    session_id2 = "scan_9_1757665129"

    result = runner.invoke(cli, [
        "reports", "all",
        "--session-id", f"{session_id1}, {session_id2}"
    ])
    assert result.exit_code == 0
    assert "Generated 3 report" in result.output
    assert "✓ Successfully generated all reports!" in result.output

def test_reports_all_with_invalid_session_id():
    runner = CliRunner()
    session_id = "non_existent_session"
    result = runner.invoke(cli, [
        "reports", "all",
        "--session-id", session_id
    ])
    assert result.exit_code == 0
    assert "No sessions found matching the criteria." in result.output
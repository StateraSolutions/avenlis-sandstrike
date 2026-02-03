from click.testing import CliRunner
from sandstrike.cli.main import cli

import tempfile
import os
import pytest

from sandstrike.main_storage import AvenlisStorage

@pytest.fixture(scope="session")
def test_db_path():
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_file.close()
    yield db_file.name
    try:
        os.remove(db_file.name)
    except PermissionError:
        pass

@pytest.fixture(autouse=True)
def patch_storage(monkeypatch, test_db_path):
    # Patch AvenlisStorage to always use the in-memory database
    def test_storage_factory(*args, **kwargs):
        kwargs["db_path"] = test_db_path
        return AvenlisStorage(*args, **kwargs)

    monkeypatch.setattr("sandstrike.cli.commands.targets.AvenlisStorage", test_storage_factory)
    monkeypatch.setattr("sandstrike.main_storage.AvenlisStorage", test_storage_factory)

# -------------------------
# TARGETS CREATE
# -------------------------

@pytest.mark.parametrize(
    "id, name, expected_exit, expected_substrings",
    [
        # First creation should succeed
        ("test", "3", 0, ["Target ID: test", "Source: local SQLite database", f"Created target: 3"]),
        # Second creation (same ID) should fail
        ("test", "3", 1, ["Error creating target: Target with ID 'test' already exists\nAborted!\n"]),
    ],
)
def test_targets_create_local_variants(id, name, expected_exit, expected_substrings):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "targets", "create",
        "--id", id,
        "--name", name,
        "--ip", "http://localhost:8080",
        "--source", "local"
    ])

    assert result.exit_code == expected_exit
    for substring in expected_substrings:
        assert substring in result.output


def test_targets_create_local_with_description():
    runner = CliRunner()
    id = "2"
    name = "TargetName"
    desc = "Desc"
    result = runner.invoke(cli, [
        "targets", "create",
        "--id", id,
        "--name", name,
        "--ip", "http://localhost:8080",
        "--description", desc,
        "--source", "local"
    ])

    assert result.exit_code == 0
    assert f"Target ID: {id}" in result.output
    assert f"Description: {desc}" in result.output
    assert f"Created target: {name}" in result.output
    assert "Source: local SQLite database" in result.output

def test_targets_create_local_short_flags():
    runner = CliRunner()
    id = "3"
    name = "TargetName"
    desc = "Desc"
    result = runner.invoke(cli, [
        "targets", "create",
        "--id", id,
        "--name", name,
        "--ip", "http://localhost:8080",
        "--description", desc,
        "-s", "local",
    ])

    assert result.exit_code == 0
    assert f"Target ID: {id}" in result.output
    assert f"Description: {desc}" in result.output
    assert f"Created target: {name}" in result.output
    assert "Source: local SQLite database" in result.output

@pytest.mark.parametrize(
    "id, name, expected_exit, expected_substrings",
    [
        # First creation should succeed
        ("4", "3", 0, ["✅ Created target: 3\nTarget ID: 4\nIP Address: http://localhost:8080\nSource: YAML file\n"]),
        # Second creation (same ID) should fail
        ("4", "3", 1, ["Error creating target: Target with ID '4' already exists\nAborted!\n"]),
    ],
)
def test_targets_create_file_variants(id, name, expected_exit, expected_substrings):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "targets", "create",
        "--id", id,
        "--name", name,
        "--ip", "http://localhost:8080",
        "--source", "file"
    ])

    assert result.exit_code == expected_exit
    for substring in expected_substrings:
        assert substring in result.output

def test_targets_create_file_with_description():
    runner = CliRunner()
    id = "5"
    name = "TargetName"
    desc = "Desc"
    result = runner.invoke(cli, [
        "targets", "create",
        "--id", id,
        "--name", name,
        "--ip", "http://localhost:8080",
        "--description", desc,
        "--source", "file"
    ])

    assert result.exit_code == 0
    assert f"Target ID: {id}" in result.output
    assert f"Description: {desc}" in result.output
    assert f"Created target: {name}" in result.output
    assert "Source: YAML file" in result.output

def test_targets_create_file_short_flags():
    runner = CliRunner()
    id = "6"
    name = "TargetName"
    desc = "Desc"
    result = runner.invoke(cli, [
        "targets", "create",
        "--id", id,
        "-n", name,
        "-i", "http://localhost:8080",
        "-d", desc,
        "-s", "file",
    ])

    assert result.exit_code == 0
    assert f"Target ID: {id}" in result.output
    assert f"Description: {desc}" in result.output
    assert f"Created target: {name}" in result.output
    assert "Source: YAML file" in result.output


# -------------------------
# TARGETS LIST
# -------------------------

def test_targets_list_explicit_all():
    runner = CliRunner()
    result = runner.invoke(cli, ["targets", "list"])

    assert result.exit_code == 0
    assert "Scan Targets" in result.output


def test_targets_list_file():
    runner = CliRunner()
    result = runner.invoke(cli, ["targets", "list", "--source", "file"])

    assert result.exit_code == 0
    assert "Scan Targets" in result.output
    # assert "Local" not in result.output


def test_targets_list_local():
    runner = CliRunner()
    result = runner.invoke(cli, ["targets", "list", "--source", "local"])

    assert result.exit_code == 0
    assert "Scan Targets" in result.output
    assert "File" not in result.output


# -------------------------
# TARGETS VIEW
# -------------------------

def test_targets_view_existing(monkeypatch):
    # First create a target
    runner = CliRunner()
    id = "6"
    name = "TargetName"
    runner.invoke(cli, [
        "targets", "create",
        "--id", id,
        "--name", name,
        "--ip", "http://localhost:8080",
        "--source", "local",
    ])

    # Now view it
    result = runner.invoke(cli, ["targets", "view", id])

    assert result.exit_code == 0
    assert f"Target ID: {id}" in result.output
    assert f"Target: {name}" in result.output
    assert "IP Address: http://localhost:8080" in result.output


def test_targets_view_missing():
    runner = CliRunner()
    id = "does_not_exist"
    result = runner.invoke(cli, ["targets", "view", id])

    assert result.exit_code == 0
    assert f"Target {id} not found" in result.output


# -------------------------
# TARGETS DELETE
# -------------------------

def test_targets_delete_existing():
    runner = CliRunner()
    id = "t1"
    name = "DeleteMe"
    # Create one first
    runner.invoke(cli, [
        "targets", "create",
        "--id", id,
        "--name", name,
        "--ip", "http://localhost:8080",
        "--source", "local",
    ])

    # Delete it
    result = runner.invoke(cli, ["targets", "delete", id], input="y\n")

    assert result.exit_code == 0
    assert f"About to delete target: {name}" in result.output
    assert f"Target ID: {id}" in result.output
    assert f"Deleted target: {name}" in result.output

def test_targets_delete_missing():
    id = "does_not_exist"
    runner = CliRunner()
    result = runner.invoke(cli, ["targets", "delete", id])

    assert result.exit_code == 0
    assert f"Target {id} not found" in result.output


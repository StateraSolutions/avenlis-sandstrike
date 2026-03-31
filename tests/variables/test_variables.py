from click.testing import CliRunner
from sandstrike.cli.main import cli

import tempfile
import os
import pytest

from sandstrike.storage import HybridStorage

# @pytest.fixture(scope="session")
# def test_db_path():
#     db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
#     db_file.close()
#     yield db_file.name
#     try:
#         os.remove(db_file.name)
#     except PermissionError:
#         pass

# @pytest.fixture(autouse=True)
# def patch_storage(monkeypatch, test_db_path):
#     # Patch AvenlisStorage to always use the in-memory database
#     def test_storage_factory(*args, **kwargs):
#         kwargs["db_path"] = test_db_path
#         return HybridStorage(*args, **kwargs)

#     monkeypatch.setattr("sandstrike.cli.commands.variables.storage", test_storage_factory)
#     monkeypatch.setattr("sandstrike.storage.HybridStorage", test_storage_factory)
        

# -------------------------
# VARIABLES LIST
# -------------------------

def test_variables_list_default():
    runner = CliRunner()
    result = runner.invoke(cli, ["variables", "list"])
    assert result.exit_code == 0
    assert "File Variables" in result.output
    assert "Local Variables" in result.output

def test_variables_list_local():
    runner = CliRunner()
    result = runner.invoke(cli, ["variables", "list", "--source", "local"])
    assert result.exit_code == 0
    assert "Local Variables" in result.output

def test_variables_list_file():
    runner = CliRunner()
    result = runner.invoke(cli, ["variables", "list", "--source", "file"])
    assert result.exit_code == 0
    assert "File Variables" in result.output

def test_variables_list_all():
    runner = CliRunner()
    result = runner.invoke(cli, ["variables", "list", "--source", "all"])
    assert result.exit_code == 0
    assert "File Variables" in result.output
    assert "Local Variables" in result.output

# -------------------------
# VARIABLES SET
# -------------------------

def test_variables_set_default():
    category = "applicationgg"
    name = "banking_appgg"
    value = "SecureBank"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "variables", "set",
        "--category", category,
        "--name", name,
        "--value", value
    ], input="local\n")
    assert result.exit_code == 0
    assert f"Variable {category}.{name} set to '{value}' in local storage" in result.output

def test_variables_set_file():
    runner = CliRunner()
    category = "application"
    name = "banking_appp"
    value = "SecureBanks"
    source = "file"
    result = runner.invoke(cli, [
        "variables", "set",
        "--category", category,
        "--name", name,
        "--value", value,
        "--source", source
    ])
    assert result.exit_code == 0
    assert f"Variable {category}.{name} set to '{value}' in \ndynamic_variables.yaml\n" in result.output


# -------------------------
# VARIABLES GET
# -------------------------

def test_variables_get_existing():
    runner = CliRunner()
    category = "application"
    name = "banking_app"
    result = runner.invoke(cli, [
        "variables", "get",
        "--category", category,
    ])
    assert result.exit_code == 0
    assert name in result.output

def test_variables_get_missing():
    runner = CliRunner()
    category = "NON_EXISTENT"
    result = runner.invoke(cli, [
        "variables", "get",
        "--category", category,
    ])
    assert result.exit_code == 0
    assert f"Category '{category}' not found in any storage" in result.output

def test_variables_get_existing_file():
    runner = CliRunner()
    category = "application"
    name = "banking_app"
    result = runner.invoke(cli, [
        "variables", "get",
        "--category", category,
        "--source", "file"
    ])
    assert result.exit_code == 0
    assert name in result.output

# -------------------------
# VARIABLES UPDATE
# -------------------------

def test_variables_update_default():
    runner = CliRunner()

    category = "applicationtt"
    name = "banking_apptt"
    value = "SecureBank"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "variables", "set",
        "--category", category,
        "--name", name,
        "--value", value
    ], input="local\n")
    value = "SecureBankPro"
    result = runner.invoke(cli, [
        "variables", "update",
        "--category", category,
        "--name", name,
        "--value", value,
    ], input="local\n")
    assert result.exit_code == 0
    assert f"Variable {category}.{name} updated in local storage" in result.output
    assert f"{value}\n" in result.output

def test_variables_update_file():
    runner = CliRunner()
    category = "application"
    name = "banking_app"
    value = "SecureBankPro"
    result = runner.invoke(cli, [
        "variables", "update",
        "--category", category,
        "--name", name,
        "--value", value,
        "--source", "file"
    ])
    assert result.exit_code == 0
    assert f"Variable {category}.{name} updated in dynamic_variables.yaml" in result.output
    assert f"{value}\n" in result.output

def test_variables_update_missing():
    runner = CliRunner()
    category = "applicat"
    name = "banking_a"
    result = runner.invoke(cli, [
        "variables", "update",
        "--category", category,
        "--name", name,
        "--value", "999"
    ], input="local\n")
    assert result.exit_code == 0
    assert f"Variable {category}.{name} not found in local storage" in result.output

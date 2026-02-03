from click.testing import CliRunner
from sandstrike.cli.main import cli
import tempfile
import os
import pytest
import re

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
    def test_storage_factory(*args, **kwargs):
        kwargs["db_path"] = test_db_path
        return AvenlisStorage(*args, **kwargs)
    monkeypatch.setattr("sandstrike.cli.commands.collections.AvenlisStorage", test_storage_factory)
    monkeypatch.setattr("sandstrike.main_storage.AvenlisStorage", test_storage_factory)

def test_create_collection_file():
    runner = CliRunner()
    name = "test_collection"
    desc = "A test collection"
    result = runner.invoke(cli, [
        "collections", "create",
        "--name", name,
        "--description", desc,
        "--source", "file"
    ])
    assert result.exit_code == 0
    assert "✅ Created collection: " + name in result.output
    assert name in result.output
    
def test_create_collection_local():
    runner = CliRunner()
    name = "test_collection"
    desc = "A test collection"
    result = runner.invoke(cli, [
        "collections", "create",
        "--name", name,
        "--description", desc,
        "--source", "local"
    ])
    print(result.output)
    assert result.exit_code == 0
    assert "✅ Created collection: " + name in result.output
    assert name in result.output

def test_list_collections():
    runner = CliRunner()
    result = runner.invoke(cli, ["collections", "list"])
    assert result.exit_code == 0
    assert "Total: " in result.output or "No collections found." in result.output

def test_list_collections_file():
    runner = CliRunner()
    result = runner.invoke(cli, ["collections", "list", "--source", "file"])
    assert result.exit_code == 0
    assert "Total: " in result.output or "No collections found." in result.output

def test_list_collections_local():
    runner = CliRunner()
    result = runner.invoke(cli, ["collections", "list", "--source", "local"])
    assert result.exit_code == 0
    assert "Total: " in result.output or "No collections found." in result.output

def test_delete_collection_file():  # For now only delete from File source
    runner = CliRunner()

    name = "test_collection"
    desc = "A test collection"
    result = runner.invoke(cli, [
        "collections", "create",
        "--name", name,
        "--description", desc,
        "--source", "file"
    ])

    match = re.search(r"Collection ID:\s*(\S+)", result.output)
    if match:
        collection_id = match.group(1)
        print(collection_id)

    result = runner.invoke(cli, [
        "collections", "delete", collection_id], input="y\n")
    assert result.exit_code == 0
    assert "Deleted collection: " in result.output

def test_delete_collection_local():  # For now only delete from File source
    runner = CliRunner()

    name = "test_collection1"
    desc = "A test collection"
    result = runner.invoke(cli, [
        "collections", "create",
        "--name", name,
        "--description", desc,
        "--source", "local"
    ])

    match = re.search(r"Collection ID:\s*(\S+)", result.output)
    if match:
        collection_id = match.group(1)
        print(collection_id)

    result = runner.invoke(cli, [
        "collections", "delete", collection_id], input="y\n")
    assert result.exit_code == 0
    assert "Deleted collection: " in result.output

def test_delete_collection_prompt():
    runner = CliRunner()
    prompt_id = "data_extraction_001"  # can be str and int
    collection_id = "collection_1762934195"
    result = runner.invoke(cli, [
        "collections", "remove-prompt", collection_id, prompt_id], input="y\n")
    assert result.exit_code == 0
    assert f"About to remove prompt: {prompt_id}" in result.output
    assert f"Removed prompt {prompt_id} from collection" in result.output

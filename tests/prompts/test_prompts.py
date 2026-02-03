from click.testing import CliRunner
from sandstrike.cli.main import cli  # Adjust import if your CLI entry point is elsewhere
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

    monkeypatch.setattr("sandstrike.cli.commands.prompts.AvenlisStorage", test_storage_factory)
    monkeypatch.setattr("sandstrike.main_storage.AvenlisStorage", test_storage_factory)
        

@pytest.mark.parametrize(
    "test_id, technique, category, text, expected_exit, expected_substrings",
    [
        # First creation should succeed
        ("test", "3", "test_cw", "prompts", 0, ["[SUCCESS] Created prompt:", "Technique:", "Category:"]),
        # Second creation (same ID) should fail
        ("test", "3", "test_cw", "prompts", 1, ["Error creating prompt: Failed to create prompt: Failed to create prompt: test \ntest_cw None\nAborted!\n"]),
    ],
)
def test_create_prompt_variants(test_id, technique, category, text, expected_exit, expected_substrings):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--text", text,
            "--source", "local"
        ]
    )

    assert result.exit_code == expected_exit
    for substring in expected_substrings:
        assert substring in result.output

def test_create_prompt_local():
    runner = CliRunner()
    test_id = "test_unique0"
    technique = "3"
    category = "test_cw"
    subcategory = "test_sub"
    text = "prompts"
    atlas = "test_atlasss"
    owasp = "test_owaspss"
    severity = "high"

    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
            "--source", "local"
        ]
    )
    assert result.exit_code == 0
    assert f"[SUCCESS] Created prompt: {test_id}" in result.output
    assert "Stored in: local SQLite database" in result.output  

def test_create_prompt_file_with_target_file_input():
    runner = CliRunner()
    test_id = "test_unique1"
    technique = "3"
    category = "test_cw"
    subcategory = "test_sub"
    text = "prompts"
    atlas = "test_atlasss"
    owasp = "test_owaspss"
    severity = "high"
    filename = "adversarial_prompts.yaml"

    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
            "--source", "file"
        ], input=f"{filename}\n"
    )
    assert result.exit_code == 0
    assert f"[SUCCESS] Created prompt: {test_id}" in result.output
    assert "Select file (enter number, filename, or 'new' for new file)" in result.output
    assert f"\nFile: {filename}" in result.output 

def test_create_prompt_no_input_source_local():
    runner = CliRunner()
    test_id = "test_unique2"
    technique = "3"
    category = "test_cw"
    subcategory = "test_sub"
    text = "prompts"
    atlas = "test_atlasss"
    owasp = "test_owaspss"
    severity = "high"

    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
        ], input="local\n"
    )
    assert result.exit_code == 0
    assert f"[SUCCESS] Created prompt: {test_id}" in result.output
    assert "Stored in: local SQLite database" in result.output


def test_create_prompt_no_input_source_file():
    runner = CliRunner()
    test_id = "test_unique3"
    technique = "3"
    category = "test_cw"
    subcategory = "test_sub"
    text = "prompts"
    atlas = "test_atlasss"
    owasp = "test_owaspss"
    severity = "high"
    filename = "adversarial_prompts.yaml"

    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
        ], input=f"file\n{filename}\n"
    )
    assert result.exit_code == 0
    assert f"[SUCCESS] Created prompt: {test_id}" in result.output
    assert f"\nFile: {filename}" in result.output

def test_list_prompts():
    runner = CliRunner()
    result = runner.invoke(cli, ["prompts", "list"])
    assert result.exit_code == 0
    assert "Adversarial Prompts" in result.output

def test_list_prompts_with_technique():
    runner = CliRunner()
    technique = "prompt_injection"
    # Now list with filter
    result = runner.invoke(cli, ["prompts", "list", "--technique", technique])
    print(result.output)
    assert result.exit_code == 0
    assert "Technique" in result.output
    assert "prompt_inj" in result.output

def test_view_prompt():
    runner = CliRunner()
    id = "system_prompt_data_retention"
    result = runner.invoke(cli, ["prompts", "view", id])
    assert result.exit_code == 0
    assert "Prompt Details" in result.output
    assert  "Prompt ID: " + id in result.output

def test_view_prompt_details():
    runner = CliRunner()
    id = "system_prompt_data_retention"
    result = runner.invoke(cli, ["prompts", "view", id, "--details"])
    assert result.exit_code == 0
    assert "Prompt Details" in result.output
    assert  "Prompt ID: " + id in result.output
    assert "Usage Statistics" in result.output
    assert "Related Sessions" in result.output

def test_delete_nonexistent_prompt():
    runner = CliRunner()
    id = "unsupported-feature-001"
    result = runner.invoke(cli, ["prompts", "delete", id])
    assert f"Prompt '{id}' not found" in result.output

def test_delete_prompt_local(): #Need to add confirmation handling
    runner = CliRunner()

    test_id = "test_unique4"
    technique = "3"
    category = "test_cw"
    subcategory = "test_sub"
    text = "prompts"
    atlas = "test_atlas"
    owasp = "test_owasp"
    severity = "high"

    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
            "--source", "local"
        ]
    )

    result = runner.invoke(cli, ["prompts", "delete", test_id], input="y\n")
    assert "About to delete prompt: " + test_id in result.output
    assert f"Deleted prompt: {test_id} (from local)" in result.output

def test_delete_prompt_file():
    runner = CliRunner()
    test_id = "test_unique5"
    technique = "3"
    category = "test_cw"
    subcategory = "test_sub"
    text = "prompts"
    atlas = "test_atlas"
    owasp = "test_owasp"
    severity = "low"
    file = "adversarial_prompts.yaml"

    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
            "--target-file", file,
            "--source", "file"
        ]
    )
    result = runner.invoke(cli, ["prompts", "delete", test_id, "--source", "file"], input="y\n")
    assert "About to delete prompt: " + test_id in result.output
    assert f"Deleted prompt: {test_id} (from file)" in result.output

# Test 1: Delete from file source when duplicate exists
# Test 2: Delete from local source when duplicate exists
@pytest.mark.parametrize(
    "choice, expected_source",
    [
        ("1", "file"),
        ("2", "local"),
    ]
)
def test_delete_prompt_duplicate(choice, expected_source):
    runner = CliRunner()
    test_id = "test_unique6"
    technique = "3"
    category = "test_cw"
    subcategory = "test_sub"
    text = "prompts"
    atlas = "test_atlas"
    owasp = "test_owasp"
    severity = "low"
    file = "adversarial_prompts.yaml"

    # Add to file first
    runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
            "--target-file", file,
            "--source", "file",
        ],
    )

    # Add to local second
    runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
            "--source", "local",
        ],
    )

    # choice = "1" (file) or "2" (local)
    result = runner.invoke(
        cli, ["prompts", "delete", test_id],
        input=f"{choice}\ny\n"
    )

    # Shared assertions
    assert f"Prompt '{test_id}' found in multiple sources:" in result.output
    assert "About to delete prompt: " + test_id in result.output
    assert f"Source: {expected_source}" in result.output
    assert f"Deleted prompt: {test_id} (from {expected_source})" in result.output

def test_delete_prompt_duplicate_delete_local():
    runner = CliRunner()
    test_id = "test_unique6"
    technique = "3"
    category = "test_cw"
    subcategory = "test_sub"
    text = "prompts"
    atlas = "test_atlas"
    owasp = "test_owasp"
    severity = "low"
    file = "adversarial_prompts.yaml"

    # Add to file first
    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
            "--target-file", file,
            "--source", "file"
        ]
    )

    # Add to local database second
    result = runner.invoke(
        cli,
        [
            "prompts", "create",
            "--id", test_id,
            "--technique", technique,
            "--category", category,
            "--subcategory", subcategory,
            "--text", text,
            "--atlas", atlas,
            "--owasp", owasp,
            "--severity", severity,
            "--source", "local"
        ]
    )

    result = runner.invoke(cli, ["prompts", "delete", test_id], input="all\ny\n")
    assert f"Prompt '{test_id}' found in multiple sources:" in result.output
    assert f"About to delete prompt '{test_id}' from all sources:" in result.output
    assert f"[SUCCESS] Deleted prompt '{test_id}' from all sources\n" in result.output

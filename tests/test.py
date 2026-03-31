from click.testing import CliRunner
from sandstrike.cli.main import cli
import tempfile
import os
import pytest

from sandstrike.main_storage import AvenlisStorage

runner = CliRunner()

# print(runner.invoke(cli, ["sessions", "export", "4", "-f", "txt"]).output)

print(runner.invoke(cli, ["collections", "import", r"C:\Users\tan88\Desktop\avenlisLibraryTest\tests\Collections\import.json"]).output)

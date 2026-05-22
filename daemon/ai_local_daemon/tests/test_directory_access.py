from tests.client import client
from src.ai_local_daemon.internal.tool_calling import FileManager
import pytest
import asyncio
from unittest.mock import patch
import os
from logger import logger


@pytest.fixture
def file_manager(config_manager):
    return FileManager(config_manager.settings)


def test_restricted_access(file_manager):
    request = asyncio.run(file_manager.provide_file("/str"))
    assert request is None


def test_accepted_access(file_manager, tmp_path):
    # create allowed directory + file
    file = tmp_path / "projects" / "hello.txt"
    file.parent.mkdir()
    file.write_text("hello")

    file_manager.settings.white_list_directories = [str(file.parent)]

    request = asyncio.run(file_manager.provide_file(str(file)))
    assert request is not None


def test_restrict_on_non_existing(file_manager):
    request = asyncio.run(file_manager.provide_file("~/non_existing_directory"))
    assert request is None


def test_neutral_directory(file_manager):
    request = asyncio.run(file_manager.provide_file("/home/"))
    assert request is None


def test_failure_on_directory(file_manager, tmp_path):
    directory = tmp_path / "projects"
    directory.mkdir()

    file_manager.settings.white_list_directories = [str(directory)]

    with pytest.raises(ValueError):
        asyncio.run(file_manager.provide_file(str(directory)))


def test_file_too_large(file_manager, tmp_path):
    # create file
    file = tmp_path / "hello.txt"
    file.write_text("small")

    file_manager.settings.white_list_directories = [str(tmp_path)]

    def fake_read_file(self, path):
        raise ValueError("File too large")

    with patch(
        "src.ai_local_daemon.tool_calling.FileManager._read_file",
        fake_read_file
    ):
        with pytest.raises(ValueError):
            asyncio.run(file_manager.provide_file(str(file)))


# Needs fix
# def test_too_many_files(file_manager, tmp_path):
#     # create many files
#     for i in range(25):
#         os.path.realpath(os.path.expanduser(tmp_path / f"file_{i}.txt"))


#     file_manager.settings.max_files = 10
#     request = file_manager._list_directory(tmp_path)
#     logger.debug(request)
#     assert request is not None

import os

import pytest

from spl_core.gcov_maid.gcov_maid import wipe_gcda_files, wipe_gcno_files


@pytest.fixture
def temp_dir(tmp_path):
    # Create a temporary directory for testing
    yield tmp_path


def test_wipe_gcno_files(temp_dir):
    # Create some gcno and obj files in the temporary directory
    gcno_files = [
        temp_dir / "file1.gcno",
        temp_dir / "subdir/file2.gcno",
        temp_dir / "file3.gcno",
    ]
    obj_files = [temp_dir / "file1.obj", temp_dir / "subdir/file2.obj"]

    # Create directories if they don't exist
    for file in gcno_files + obj_files:
        os.makedirs(file.parent, exist_ok=True)

    # Create the files
    for file in gcno_files + obj_files:
        file.touch()

    # Call the function under test
    wipe_gcno_files(temp_dir)

    # Check that the gcno files without corresponding obj files are deleted
    assert gcno_files[0].exists()
    assert gcno_files[1].exists()
    assert not gcno_files[2].exists()

    # Check that the obj files are not deleted
    assert obj_files[0].exists()
    assert obj_files[1].exists()


def test_wipe_gcno_files_keeps_notes_with_unix_object(temp_dir):
    # On Unix/Linux CMake names object files ".o" (not ".obj").
    # A .gcno with a sibling .o object must be considered valid and kept.
    gcno_files = [
        temp_dir / "file1.c.gcno",
        temp_dir / "subdir/file2.c.gcno",
        temp_dir / "orphan.c.gcno",
    ]
    obj_files = [temp_dir / "file1.c.o", temp_dir / "subdir/file2.c.o"]

    for file in gcno_files + obj_files:
        os.makedirs(file.parent, exist_ok=True)
    for file in gcno_files + obj_files:
        file.touch()

    wipe_gcno_files(temp_dir)

    # gcno files with a corresponding .o object are kept
    assert gcno_files[0].exists()
    assert gcno_files[1].exists()
    # the orphan (no object at all) is removed
    assert not gcno_files[2].exists()

    # object files are never touched
    assert obj_files[0].exists()
    assert obj_files[1].exists()


def test_wipe_gcda_files(temp_dir):
    # Create some gcda files in the temporary directory
    gcda_files = [
        temp_dir / "file1.gcda",
        temp_dir / "subdir/file2.gcda",
        temp_dir / "subdir/file3.gcda",
    ]
    # Create some other files in the temporary directory
    other_files = [temp_dir / "file1.obj", temp_dir / "subdir/file2.gcno"]

    # Create directories if they don't exist
    for file in gcda_files + other_files:
        os.makedirs(file.parent, exist_ok=True)
    for file in gcda_files + other_files:
        file.touch()

    # Call the function under test
    wipe_gcda_files(temp_dir)

    # Check that the gcda files are deleted
    assert not gcda_files[0].exists()
    assert not gcda_files[1].exists()
    assert not gcda_files[2].exists()

    # Check that the other files are not deleted
    assert other_files[0].exists()
    assert other_files[1].exists()

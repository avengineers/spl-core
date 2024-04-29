from time import sleep

from utils import DirectoryTracker, create_clean_test_dir


class TestDirectoryTracker:
    def test_directory_tracker_update_status(self):
        out_dir = create_clean_test_dir("test_directory_tracker_update_status")
        out_dir.write_file("file1.txt")
        out_dir.write_file("file2.txt")
        tracker = DirectoryTracker(out_dir.path)
        status = tracker.get_status()
        assert len(status.unchanged_files) == 2
        assert len(status.changed_files) == 0
        assert len(status.new_files) == 0
        assert len(status.deleted_files) == 0

        """add a new file"""
        out_dir.write_file("file3.txt")
        status = tracker.get_status()
        assert len(status.unchanged_files) == 2
        assert len(status.changed_files) == 0
        assert len(status.new_files) == 1
        assert len(status.deleted_files) == 0

        """delete one file"""
        out_dir.delete_file("file2.txt")
        status = tracker.get_status()
        assert len(status.unchanged_files) == 1
        assert len(status.changed_files) == 0
        assert len(status.new_files) == 1
        assert len(status.deleted_files) == 1

        """override one file"""
        # Workaround: for whatever reason we need to wait here abit
        # to get a changed file on GitHub Actions.
        # (Is Windows so fast? Our is the time counter so inaccurate?)
        sleep(0.1)
        out_dir.write_file("file1.txt")
        status = tracker.get_status()
        assert len(status.unchanged_files) == 0
        assert len(status.changed_files) == 1
        assert len(status.new_files) == 1
        assert len(status.deleted_files) == 1
        """create empty folder"""
        out_dir.joinpath("some_dir").mkdir()
        status = tracker.get_status()
        assert len(status.unchanged_files) == 0
        assert len(status.changed_files) == 1
        assert len(status.new_files) == 1
        assert len(status.deleted_files) == 1

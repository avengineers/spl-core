import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Script with command line options")
    parser.add_argument("--working-dir", help="Working directory", required=True)  # Make the option mandatory
    parser.add_argument("--wipe-all-gcda", action="store_true", help="Wipe all gcda files recursively")
    parser.add_argument(
        "--wipe-orphaned-gcno",
        action="store_true",
        help="Wipe orphaned gcno files recursively",
    )

    args = parser.parse_args()

    # Access the command line options
    working_dir = Path(args.working_dir)  # Convert the string to a Path object
    wipe_gcda = bool(args.wipe_all_gcda)  # Convert the switch value to boolean
    wipe_gcno = bool(args.wipe_orphaned_gcno)  # Convert the switch value to boolean

    if wipe_gcda:
        wipe_gcda_files(working_dir)

    if wipe_gcno:
        wipe_gcno_files(working_dir)


def wipe_gcda_files(working_dir: Path) -> None:
    for file in working_dir.glob("**/*.gcda"):
        print(f"Deleting obsolete coverage data file: {file}")
        file.unlink()


def wipe_gcno_files(working_dir: Path) -> None:
    # CMake names compiled objects ".obj" on Windows and ".o" on Unix/Linux.
    # A .gcno is only orphaned when no object file exists under either name.
    object_suffixes = (".obj", ".o")
    for file in working_dir.glob("**/*.gcno"):
        if not any(file.with_suffix(suffix).exists() for suffix in object_suffixes):
            print(f"Deleting obsolete coverage notes file: {file}")
            file.unlink()


if __name__ == "__main__":
    main()

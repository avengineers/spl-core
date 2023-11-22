import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Script with command line options")
    parser.add_argument(
        "--working-dir", help="Working directory", required=True
    )  # Make the option mandatory
    parser.add_argument("--wipe-gcda", action="store_true", help="Wipe gcda files")
    parser.add_argument("--wipe-gcno", action="store_true", help="Wipe gcno files")

    args = parser.parse_args()

    # Access the command line options
    working_dir = Path(args.working_dir)  # Convert the string to a Path object
    wipe_gcda = bool(args.wipe_gcda)  # Convert the switch value to boolean
    wipe_gcno = bool(args.wipe_gcno)  # Convert the switch value to boolean

    if wipe_gcda:
        wipe_gcda_files(working_dir)

    if wipe_gcno:
        wipe_gcno_files(working_dir)


def wipe_gcda_files(working_dir):
    for file in working_dir.glob("**/*.gcda"):
        print(f"Deleting obsolete coverage data file: {file}")
        file.unlink()


def wipe_gcno_files(working_dir):
    for file in working_dir.glob("**/*.gcno"):
        obj_file = file.with_suffix(".obj")
        if not obj_file.exists():
            print(f"Deleting obsolete coverage notes file: {file}")
            file.unlink()


if __name__ == "__main__":
    main()

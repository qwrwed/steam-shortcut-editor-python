import json
import logging
from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from pprint import pprint
from shutil import copy

from steam_shortcut_editor import parse_file, write_file

LOGGER = logging.getLogger(__name__)


class ProgramArgsNamespace(Namespace):
    steam_user_id: str
    steam_directory: Path


def get_args() -> ProgramArgsNamespace:
    parser = ArgumentParser()
    parser.add_argument(
        "-u",
        "--steam-user-id",
    )
    parser.add_argument(
        "-d",
        "--steam-directory",
        default=Path("C:/Program Files (x86)/Steam"),
        type=Path,
        help="default: %(default)s",
    )
    args = parser.parse_args(namespace=ProgramArgsNamespace())
    if not args.steam_user_id:
        userdata_path = Path(args.steam_directory, "userdata")
        steam_user_ids = [
            path.name for path in userdata_path.iterdir() if path.is_dir()
        ]
        if len(steam_user_ids) == 1:
            [args.steam_user_id] = steam_user_ids
        else:
            raise ValueError(
                f"Could not automatically get steam user ID (found user IDs: {steam_user_ids})"
            )

    return args


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # return obj.isoformat()
            return int(obj.timestamp())
        return super().default(obj)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = get_args()
    vdf_path = Path(
        args.steam_directory, "userdata", args.steam_user_id, "config", "shortcuts.vdf"
    )

    vdf_copy_path = Path(".", vdf_path.name)
    LOGGER.info("Copying VDF at '%s' to '%s'", vdf_path, vdf_copy_path.resolve())
    copy(vdf_path, vdf_copy_path)

    LOGGER.info("Converting VDF to JSON...")
    obj = parse_file(vdf_path)

    json_path = vdf_copy_path.with_suffix(".json")
    LOGGER.info("Writing JSON to '%s'", json_path.resolve())
    with open(json_path, "w") as f:
        json.dump(obj, f, indent=4, cls=DateTimeEncoder)


if __name__ == "__main__":
    main()

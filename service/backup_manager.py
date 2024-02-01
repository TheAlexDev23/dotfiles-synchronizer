import os

import path_translator
import tracking_state

from cmd_manager import exec_cmd


def backup_all_files():
    for path in tracking_state.base_paths:
        if os.path.isdir(path):
            backup_directory(path)
        else:
            backup_file(path)


def backup_directory(dir: str) -> None:
    print(f"Backing up directory {dir}")

    backup_dir = path_translator.to_backup_path(dir)
    upper_backup_dir = os.path.join(backup_dir, "..")

    exec_cmd(f"mkdir -p {backup_dir}")
    exec_cmd(f"cp -r {dir} {upper_backup_dir}")


def backup_file(path: str) -> None:
    print(f"Backing up file {path}")

    backup_dir = path_translator.to_backup_path(path)

    exec_cmd(f"mkdir -p {backup_dir}")
    exec_cmd(f"cp {path} {backup_dir}")


def delete_backed_up_path(path: str):
    path = path_translator.to_backup_path(path)
    exec_cmd(f"rm -rf {path}")

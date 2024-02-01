from ctypes import ArgumentError
import constants


def to_backup_path(path: str) -> str:
    # to make pyright stfu
    assert constants.HOME is not None

    if not path.startswith(constants.HOME):
        raise ArgumentError("Path not located in /home/user are not supported")

    return path.replace(constants.HOME, "../home")

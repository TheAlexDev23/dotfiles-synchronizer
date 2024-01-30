#!/usr/bin/env python

import sys
import os
import subprocess
import json
import time
from datetime import datetime

from inotify_simple import INotify, flags

import commit_message_generation


# Polling rate for file changes in seconds. Isn't as important, just make sure that it's not 0 if you use editors like neovim.
RATE = 0.5

VERBOSE_LOGGING = False

# Used in development, if True will just print the supposed commands without executing them
NO_BACKUP = False

# Time since last commit in order to push. Used to prevent rate limits.
PUSH_RATE = 30

# Experimental. Use GPT for commit messages. Requires OPENAI_KEY environment variable
USE_OPENAI = False

HOME = os.environ.get("HOME")
if HOME is None:
    print("HOME environment variable is nonexistent")
    exit(1)

CONFIG = HOME + "/.config/synchronization_targets.json"

config_notify: INotify
dotfiles_notify: INotify

awaiting_push = False
time_since_awaiting_push: float = 0


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


base_paths = {}
all_tracked_paths = {}


def track_config():
    global config_notify
    config_notify = INotify()
    watch_flags = flags.CREATE | flags.DELETE | flags.MODIFY | flags.DELETE_SELF

    config_notify.add_watch(CONFIG, watch_flags)


def backup_initial_files():
    print("Performing initial backup")

    with open(CONFIG, "r") as fp:
        data = json.load(fp)

    for dir in data["directories"]:
        dir = os.path.expanduser(dir)
        backup_directory(dir)

    for path in data["files"]:
        path = os.path.expanduser(path)
        backup_file(path)

    git_commit("initial backup")


def check_for_changes():
    global dotfiles_notify, config_notify

    while True:
        check_config_changes()
        check_tracked_files()

        if awaiting_push and time.time() - time_since_awaiting_push >= PUSH_RATE:
            git_push()

        time.sleep(RATE)


def parse_config(exit_on_failure=True):
    try:
        with open(CONFIG, "r") as fp:
            data = json.load(fp)
    except:
        eprint("Could not load config. ")
        if exit_on_failure:
            exit(1)
        else:
            # Gotta exit and keep previous dotfiles_notify because we wont be able to parse data
            return

    track_dotfiles(data)


def track_dotfiles(data) -> None:
    global dotfiles_notify
    dotfiles_notify = INotify()

    global all_tracked_paths, base_paths

    all_tracked_paths = {}
    base_paths = {}

    for path in data["directories"]:
        path = os.path.expanduser(path)
        base_path = path
        print(f"Watching {path}")
        add_watch(path, base_path)

        for root, dirs, _ in os.walk(path):
            for directory in dirs:
                path = os.path.join(root, directory)
                print(f"Watching {path}")
                add_watch(path, base_path)

    for path in data["files"]:
        path = os.path.expanduser(path)
        print(f"Watching {path}")
        add_watch(path, path)


def add_watch(path: str, base_path: str) -> None:
    watch_flags = (
        flags.CREATE
        | flags.DELETE
        | flags.MODIFY
        | flags.DELETE_SELF
        | flags.MOVED_FROM
        | flags.MOVED_TO
    )

    global dotfiles_notify, all_tracked_paths

    try:
        wd = dotfiles_notify.add_watch(path, watch_flags)
    except FileNotFoundError:
        print(f"Could not track {path}, file doesn't exist")
        return

    add_to_base_paths(base_path, wd)
    all_tracked_paths[wd] = path


def add_to_base_paths(path: str, wd):
    if path not in base_paths:
        base_paths[path] = []

    base_paths[path].append(wd)


def check_config_changes():
    global config_notify

    changes = config_notify.read(0, 1)

    if len(changes) == 0:
        return

    for change in changes:
        for flag in flags.from_mask(change.mask):
            if flag is flags.IGNORED:
                track_config()

    parse_config(False)


def check_tracked_files():
    global dotfiles_notify

    changes = dotfiles_notify.read(0, 1)

    if len(changes) == 0:
        return

    # Paths to delete before applying changed_paths. Used when subfiles are deleted.
    force_change = set()
    changed_paths = set()
    deleted_paths = set()

    for change in changes:
        base_path = get_base_path(change.wd)
        print(f"Detected changes in {base_path}")

        if deleted_path(change):
            deleted_paths.add(base_path)
        else:
            changed_paths.add(base_path)
            if deleted_subfile(change):
                force_change.add(base_path)

        if VERBOSE_LOGGING:
            print(f"Change {change}")
            log_change_flags(change)

        retrack_file_if_necessary(change, base_path)

    for change in force_change:
        delete_backed_up_path(change)

    for change in changed_paths:
        if os.path.isdir(change):
            backup_directory(change)
        else:
            backup_file(change)

    for deletion in deleted_paths:
        delete_backed_up_path(deletion)

    commit_message = "\nChanges to:"
    for change in changed_paths:
        commit_message += " " + change.replace(HOME, "./home")
    commit_message += "\nDeleted: "
    for deletion in deleted_paths:
        commit_message += " " + deletion.replace(HOME, "./home")

    git_commit(commit_message)


def get_base_path(wd) -> str:
    for key, value in base_paths.items():
        if wd in value:
            return key

    raise ValueError("Invalid argument")


def deleted_path(change) -> bool:
    for flag in flags.from_mask(change.mask):
        if flag is flags.DELETE_SELF:
            return True

    return False


def deleted_subfile(change) -> bool:
    for flag in flags.from_mask(change.mask):
        if flag is flags.DELETE:
            return True

    return False


def log_change_flags(change):
    for flag in flags.from_mask(change.mask):
        print(next((flag.name for _flag in flags if _flag.value == flag), None))  # type: ignore


def retrack_file_if_necessary(change, base_path):
    # I don't really understand how the ignored flag works, I just know that changes
    # with it need to be retracked or they won't be tracked anymore
    for flag in flags.from_mask(change.mask):
        if flag is not flags.IGNORED:
            continue

        path = all_tracked_paths[change.wd]

        if not os.path.exists(path):
            return

        add_watch(path, base_path)


def backup_directory(dir: str) -> None:
    print(f"Backing up directory {dir}")

    backup_dir = dir.replace(HOME, "./home")
    upper_backup_dir = os.path.join(backup_dir, "..")

    exec_cmd(f"mkdir -p {backup_dir}")
    exec_cmd(f"cp -r {dir} {upper_backup_dir}")


def backup_file(path: str) -> None:
    print(f"Backing up file {path}")

    backup_dir = os.path.dirname(path.replace(HOME, "./home"))

    exec_cmd(f"mkdir -p {backup_dir}")
    exec_cmd(f"cp {path} {backup_dir}")


def delete_backed_up_path(path: str):
    path = path.replace(HOME, "./home")
    exec_cmd(f"rm -rf {path}")


def git_commit(commit_message: str | None = None):
    global awaiting_push, time_since_awaiting_push

    awaiting_push = True
    time_since_awaiting_push = time.time()

    if commit_message is None:
        commit_message = str(datetime.now())

    exec_cmd("git add .")

    if USE_OPENAI:
        commit_message = commit_message_generation.get_commit_message()

    exec_cmd(f'git commit -m "Automated Backup: {commit_message}"')


def git_push():
    global awaiting_push
    awaiting_push = False

    exec_cmd("git push")


def exec_cmd(cmd: str) -> None:
    if NO_BACKUP:
        print(cmd)
    else:
        subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    parse_config()
    track_config()

    backup_initial_files()
    check_for_changes()

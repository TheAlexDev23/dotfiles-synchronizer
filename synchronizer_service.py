#!/usr/bin/env python

import sys
import os
import subprocess
import json
import time

from datetime import datetime

from inotify_simple import INotify, flags

# Polling rate for file changes in seconds
RATE = 0.5

HOME = os.environ.get("HOME")
if HOME is None:
    print("HOME environment variable is nonexistent")
    exit(1)

CONFIG = HOME + "/.config/synchronization_targets.json"

VERBOSE_LOGGING = False

# Mainly used in development. If False, won't commit
COMMIT = True

# Time since last commit to push
PUSH_RATE = 30

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

    global dotfiles_notify
    wd = dotfiles_notify.add_watch(path, watch_flags)
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

    changed_dirs = set()
    for change in changes:
        base_path = get_base_path(change.wd)
        print(f"Detected changes in {base_path}")
        changed_dirs.add(base_path)

        if VERBOSE_LOGGING:
            print(f"Change {change}")
            log_change_flags(change)

        retrack_file_if_necessary(change, base_path)

    for change in changed_dirs:
        if os.path.isdir(change):
            backup_directory(change)
        else:
            backup_file(change)

    commit_message = "Changes to "
    for change in changed_dirs:
        commit_message += os.path.basename(change) + " "

    git_commit(commit_message)


def get_base_path(wd) -> str:
    for key, value in base_paths.items():
        if wd in value:
            return key

    raise ValueError("Invalid argument")


def log_change_flags(change):
    for flag in flags.from_mask(change.mask):
        print(next((flag.name for _flag in flags if _flag.value == flag), None))


def retrack_file_if_necessary(change, base_path):
    for flag in flags.from_mask(change.mask):
        if flag is not flags.IGNORED:
            continue

        path = all_tracked_paths[change.wd]

        add_watch(path, base_path)


def backup_directory(dir: str) -> None:
    print(f"Backing up directory {dir}")

    backup_dir = dir.replace(HOME, "./home")

    subprocess.run(["mkdir", "-p", backup_dir])
    subprocess.run(["cp", "-r", dir, backup_dir + "/.."])


def backup_file(path: str) -> None:
    print(f"Backing up file {path}")

    backup_dir = os.path.dirname(path.replace(HOME, "./home"))

    subprocess.run(["mkdir", "-p", backup_dir])
    subprocess.run(["cp", path, backup_dir])


def git_commit(commit_message: str | None = None):
    global awaiting_push, time_since_awaiting_push

    awaiting_push = True
    time_since_awaiting_push = time.time()

    if commit_message is None:
        commit_message = str(datetime.now())

    if not COMMIT:
        print(f"Commit with message {commit_message}")
        return

    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"Automated update: {commit_message}"])


def git_push():
    global awaiting_push
    awaiting_push = False

    if not COMMIT:
        print("Git push")
        return

    subprocess.run(["git", "push"])


if __name__ == "__main__":
    parse_config()
    track_config()

    backup_initial_files()
    check_for_changes()

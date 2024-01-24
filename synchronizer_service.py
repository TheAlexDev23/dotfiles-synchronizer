#!/usr/bin/env python

import sys
import os
import subprocess
import json
import time

from datetime import datetime

from inotify_simple import INotify, flags

# Polling rate for file changes in seconds
RATE = 1

HOME = os.environ.get("HOME")
if HOME is None:
    print("HOME environment variable is nonexistent")
    exit(1)

CONFIG = HOME + "/.config/synchronization_targets.json"

VERBOSE_LOGGING = False


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


full_paths = {}


def check_for_changes():
    global dotfiles_notify

    parse_config()

    os.mkdir(HOME + "/.config/polybar/haha")

    while True:
        for change in dotfiles_notify.read():
            if not VERBOSE_LOGGING:
                continue
            print(change + " " + get_full_path(change.wd))
            for flag in flags.from_mask(change.mask):
                print(next((flag.name for _flag in flags if _flag.value == flag), None))

        # git_commit()

        time.sleep(RATE)


def parse_config():
    try:
        with open(CONFIG, "r") as fp:
            data = json.load(fp)

        global dotfiles_notify
    except:
        eprint("Could not load config. Exiting...")
        exit(1)

    dotfiles_notify = get_inotify(data)


def get_inotify(data) -> INotify:
    inotify = INotify()
    watch_flags = (
        flags.CREATE
        | flags.DELETE
        | flags.MODIFY
        | flags.DELETE_SELF
        | flags.MOVED_FROM
        | flags.MOVED_TO
    )

    for path in data["directories"]:
        path = os.path.expanduser(path)
        print(f"Watching {path}")
        wd = inotify.add_watch(path, watch_flags)
        add_to_full_paths(path, wd)

        for root, dirs, _ in os.walk(path):
            for directory in dirs:
                path = os.path.join(root, directory)
                print(f"Watching {path}")
                wd = inotify.add_watch(path, watch_flags)
                add_to_full_paths(path, wd)

    for path in data["files"]:
        path = os.path.expanduser(path)
        print(f"Watching {path}")
        inotify.add_watch(path, watch_flags)

    return inotify


def add_to_full_paths(path: str, wd):
    if path not in full_paths:
        full_paths[path] = []

    full_paths[path].append(wd)


def get_full_path(wd) -> str | None:
    for key, value in full_paths.items():
        if wd in value:
            return key
    return None


def backup_directory(dir: str) -> None:
    print(f"Change in directory {dir}")

    backup_dir = dir.replace(HOME, "./home")

    subprocess.run(["mkdir", "-p", backup_dir])
    subprocess.run(["cp", "-r", dir, backup_dir + "/.."])

    git_commit()


def backup_file(path: str) -> None:
    print(f"Change in file {path}")

    backup_dir = os.path.dirname(path.replace(HOME, "./home"))

    subprocess.run(["mkdir", "-p", backup_dir])
    subprocess.run(["cp", path, backup_dir])

    git_commit()


def git_commit():
    current_datetime = datetime.now()

    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"Automated update {current_datetime}"])
    subprocess.run(["git", "push", "origin", "main"])


check_for_changes()

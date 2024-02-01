#!/usr/bin/env python

import sys
import os
import json
import time

from inotify_simple import INotify, flags

import flag_helper
import constants
import path_translator
import git_manager
import tracking_state
import backup_manager


config_notify: INotify
dotfiles_notify: INotify


def track_config():
    global config_notify
    config_notify = INotify()
    watch_flags = flags.CREATE | flags.DELETE | flags.MODIFY | flags.DELETE_SELF

    config_notify.add_watch(constants.CONFIG, watch_flags)


def backup_initial_files():
    print("Performing initial backup")

    backup_manager.backup_all_files()

    git_manager.commit("initial backup")


def check_for_changes():
    global dotfiles_notify, config_notify

    while True:
        check_config_changes()
        check_tracked_files()

        git_manager.push_if_necessary()

        time.sleep(constants.RATE)


def parse_config(exit_on_failure=True):
    try:
        with open(constants.CONFIG, "r") as fp:
            data = json.load(fp)
    except:
        sys.stderr.write("Could not load config.\n")
        if exit_on_failure:
            exit(1)
        else:
            # Gotta exit and keep previous dotfiles_notify because we wont be able to parse data
            return

    track_dotfiles(data)


def track_dotfiles(data) -> None:
    global dotfiles_notify
    dotfiles_notify = INotify()

    tracking_state.all_tracked_paths = {}
    tracking_state.base_paths = {}

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

    try:
        wd = dotfiles_notify.add_watch(path, watch_flags)
    except FileNotFoundError:
        print(f"Could not track {path}, file doesn't exist")
        return

    add_to_base_paths(base_path, wd)
    tracking_state.all_tracked_paths[wd] = path


def add_to_base_paths(path: str, wd):
    if path not in tracking_state.base_paths:
        tracking_state.base_paths[path] = []

    tracking_state.base_paths[path].append(wd)


def check_config_changes():
    global config_notify

    changes = config_notify.read(0, 1)

    if len(changes) == 0:
        return

    for change in changes:
        if flag_helper.has_ignored_flag(change):
            track_config()

    parse_config(False)
    backup_manager.backup_all_files()
    git_manager.commit("synchronization targets changed")


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

        if flag_helper.deleted_path(change):
            deleted_paths.add(base_path)
        else:
            changed_paths.add(base_path)
            if flag_helper.deleted_subfile(change):
                force_change.add(base_path)

        if constants.VERBOSE_LOGGING:
            print(f"Change {change}")
            flag_helper.print_flags(change)

        retrack_file_if_necessary(change, base_path)

    for change in force_change:
        backup_manager.delete_backed_up_path(change)

    for change in changed_paths:
        if os.path.isdir(change):
            backup_manager.backup_directory(change)
        else:
            backup_manager.backup_file(change)

    for deletion in deleted_paths:
        backup_manager.delete_backed_up_path(deletion)

    commit_message = "\nChanges to:"
    for change in changed_paths:
        commit_message += " " + path_translator.to_backup_path(change)
    commit_message += "\nDeleted: "
    for deletion in deleted_paths:
        commit_message += " " + path_translator.to_backup_path(deletion)

    git_manager.commit(commit_message)


def get_base_path(wd) -> str:
    for key, value in tracking_state.base_paths.items():
        if wd in value:
            return key

    raise ValueError("Invalid argument")


def retrack_file_if_necessary(change, base_path):
    # I don't really understand how the ignored flag works, I just know that changes
    # with it need to be retracked or they won't be tracked anymore
    if not flag_helper.has_ignored_flag(change):
        return

    path = tracking_state.all_tracked_paths[change.wd]

    # Sometimes deleted files also get marked with IGNORED, so retracking them will be a no no
    if not os.path.exists(path):
        return

    add_watch(path, base_path)


if __name__ == "__main__":
    parse_config()
    track_config()

    backup_initial_files()
    check_for_changes()

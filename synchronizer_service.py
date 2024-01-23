#!/usr/bin/env python

import os
import subprocess
import atexit
import hashlib
import json
import time

from datetime import datetime

HOME = os.environ.get("HOME")
if HOME is None:
    print("HOME environment variable is non existant")
    exit(1)

dir_hashes = {}
file_hashes = {}


def load_hashes():
    if not os.path.exists(os.path.abspath("./save.json")):
        return

    with open("save.json", "r") as fp:
        data = json.load(fp)

    global dir_hashes, file_hashes

    dir_hashes = data["directories"]
    file_hashes = data["files"]


def save_hashes():
    saved_hashes = {"directories": dir_hashes, "files": file_hashes}

    with open("save.json", "w") as fp:
        json.dump(saved_hashes, fp)


def check_for_changes():
    with open("targets.json", "r") as fp:
        data = json.load(fp)

    while True:
        check_for_directories(data)

        check_for_files(data)

        time.sleep(3)


def check_for_directories(data):
    for dir in data["directories"]:
        # Python struggles to open directories with ~ for some reason
        dir = os.path.expanduser(dir)

        dir_hash = hash_directory(dir)

        if dir not in dir_hashes or dir_hashes[dir] != dir_hash:
            backup_directory(dir)

        dir_hashes[dir] = dir_hash


def check_for_files(data):
    for file_path in data["files"]:
        file_path = os.path.expanduser(file_path)

        file_hash = hash_file(file_path)

        if file_path not in file_hashes or file_hashes[file_path] != file_hash:
            backup_file(file_path)

        file_hashes[file_path] = file_hash


def hash_directory(directory_path: str) -> str:
    hasher = hashlib.sha256()
    for root, dirs, files in os.walk(directory_path):
        dirs.sort()
        files.sort()
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            hasher.update(hash_directory(dir_path).encode("utf-8"))
        for file_name in files:
            file_path = os.path.join(root, file_name)
            with open(file_path, "rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    hasher.update(chunk)

    return hasher.hexdigest()


def hash_file(file_path: str) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


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


load_hashes()
atexit.register(save_hashes)

check_for_changes()

import time
from datetime import datetime

from cmd_manager import exec_cmd
import constants
import commit_message_generation

awaiting_push = False
time_since_awaiting_push = 0


def commit(commit_message: str | None = None):
    global awaiting_push, time_since_awaiting_push

    awaiting_push = True
    time_since_awaiting_push = time.time()

    if commit_message is None:
        commit_message = str(datetime.now())

    exec_cmd("git add .")

    if constants.USE_OPENAI:
        commit_message = commit_message_generation.get_commit_message()

    exec_cmd(f'git commit -m "Automated Backup: {commit_message}"')


def push_if_necessary():
    if time.time() - time_since_awaiting_push >= constants.PUSH_RATE:
        _git_push()


def _git_push():
    global awaiting_push
    awaiting_push = False

    exec_cmd("git push")

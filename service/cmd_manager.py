import subprocess

import constants


def exec_cmd(cmd: str) -> None:
    if constants.NO_BACKUP:
        print(cmd)
    else:
        subprocess.run(cmd, shell=True)

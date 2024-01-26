<h1 align="center">Dotfiles Synchronizer</h1>

Automatically synchronize any of your configurations to git. A working example can be seen [here](https://github.com/TheAlexDev23/dotfiles)

## Installation

1. **Fork** this repository
2. Clone the forked repo (preferably with ssh, as this program will also automatically push and you won't be able to input password/passkey)
3. Run systemd_setup.sh (if you have systemd) 
4. Profit

You can configure the directories or inidividual files that you want to synchronize by modifying `~/.config/synchronization_targets.json`

The syntax is quite simple:

```json
{
    "directories": [
        "~/path/to/your/dir1",
        "~/path/to/your/dir2",
        "~/path/to/your/dir3"
    ],
    "files": [
        "~/path/to/your/file.1",
        "~/path/to/your/file.2",
        "~/path/to/your/file.3"
    ]
}
```

## Other configuration

synchronizer_service.py:
```python
# Polling rate for file changes in seconds. Isn't as important, just make sure that it's not 0 if you use editors like neovim.
RATE = 0.5

VERBOSE_LOGGING = False

# Mainly used in development. If False, will not commit/push just log.
COMMIT = True

# Time since last commit in order to push. Used to prevent rate limits.
PUSH_RATE = 30

# Experimental. Use GPT for commit messages. Requires OPENAI_KEY environment variable
USE_OPENAI = False
```


## What if I don't have systemd?
I don't really have experience with systemd alternatives, but feel free to open a pr.

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
# Polling rate for changes in seconds
RATE = 30
```


## What if I don't have systemd?
I don't really have experience with systemd alternatives, but feel free to open a pr.

<h1 align="center">Dotfiles Synchronizer</h1>

Automatically synchronize any of your configurations to git.

## Installation

1. **Fork** this repository
2. Clone the forked repo (preferably with ssh, as this program will also automatically push and you won't be able to input password/passkey)
3. Edit targets.json and add any directories/files that you want to synchronize
4. Edit the HOME variable in synchronizer_service.py to your home folder
5. Run systemd_setup.sh (if you have systemd) NOTE: it requires sudo abilities for your user
6. Profit

## Other configuration

synchronizer_service.py:
```python
# Polling rate for changes in seconds
RATE = 30
```


## What if I don't have systemd?
I don't really have experience with systemd alternatives, but feel free to open a pr.

import os

RATE = 0.5

VERBOSE_LOGGING = False
NO_BACKUP = True
PUSH_RATE = 30

USE_OPENAI = False

HOME = os.environ.get("HOME")
if HOME is None:
    print("HOME environment variable is nonexistent")
    exit(1)

CONFIG = HOME + "/.config/synchronization_targets.json"

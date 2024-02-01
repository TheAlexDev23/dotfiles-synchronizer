from inotify_simple import flags


def has_ignored_flag(change):
    for flag in flags.from_mask(change.mask):
        if flag is flags.IGNORED:
            return True

    return False


def print_flags(change):
    for flag in flags.from_mask(change.mask):
        print(next((flag.name for _flag in flags if _flag.value == flag), None))  # type: ignore


def deleted_path(change) -> bool:
    for flag in flags.from_mask(change.mask):
        if flag is flags.DELETE_SELF:
            return True

    return False


def deleted_subfile(change) -> bool:
    for flag in flags.from_mask(change.mask):
        if flag is flags.DELETE:
            return True

    return False

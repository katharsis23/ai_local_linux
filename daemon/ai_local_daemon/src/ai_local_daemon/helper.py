import os


def normalize_path(path: str) -> str:
    return os.path.realpath(os.path.expanduser(path))



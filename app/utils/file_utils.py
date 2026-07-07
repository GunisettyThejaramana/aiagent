from pathlib import Path


def file_exists(path):

    return Path(path).exists()


def get_extension(path):

    return Path(path).suffix.lower()


def get_filename(path):

    return Path(path).name


def get_size(path):

    return Path(path).stat().st_size
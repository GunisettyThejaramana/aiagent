from datetime import datetime


def current_time():

    return datetime.now()


def format_bytes(size):

    units = ["B", "KB", "MB", "GB"]

    index = 0

    while size > 1024 and index < len(units) - 1:

        size /= 1024

        index += 1

    return f"{size:.2f} {units[index]}"
"""Scans the top level of a folder for files matching the given extensions."""

import os


def scan_folder(folder, extensions):
    """Return [(full_path, file_name, size_bytes)] — top-level files only, never recursive."""
    matches = []
    with os.scandir(folder) as entries:
        for entry in entries:
            if entry.is_file() and os.path.splitext(entry.name)[1].lstrip(".").lower() in extensions:
                matches.append((entry.path, entry.name, entry.stat().st_size))
    matches.sort(key=lambda m: m[1].lower())
    return matches

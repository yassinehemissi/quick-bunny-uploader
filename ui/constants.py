"""Shared UI constants."""

import os

API_URL = os.environ.get("BUNNY_API_URL", "http://127.0.0.1:3999")
UPLOAD_TIMEOUT = 600  # seconds without socket progress before one upload gives up

# Row label width (in characters) so labels of different components align.
LABEL_WIDTH = 12

TYPE_GROUPS = {
    "Images": ("jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "avif", "ico", "tiff"),
    "Videos": ("mp4", "webm", "mov", "mkv", "avi", "m4v", "flv", "wmv"),
    "Audio": ("mp3", "wav", "ogg", "m4a", "flac", "aac", "opus"),
    "Documents": ("pdf", "doc", "docx", "txt", "md", "csv", "xls", "xlsx", "ppt", "pptx", "json", "xml"),
    "Archives": ("zip", "rar", "7z", "tar", "gz", "bz2"),
}

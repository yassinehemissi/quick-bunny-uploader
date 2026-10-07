"""Listbox showing the matched top-level files."""

import tkinter as tk
from tkinter import ttk

from utils import human_size


class FileList(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Matched files (top level only)", padding=4)

        self.listbox = tk.Listbox(self, height=7)
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def set_files(self, matches):
        """matches: [(full_path, file_name, size_bytes)]"""
        self.listbox.delete(0, tk.END)
        for _path, name, size in matches:
            self.listbox.insert(tk.END, f"{name}  —  {human_size(size)}")

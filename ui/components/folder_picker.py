"""Folder picker row: label + path entry + Browse button."""

import os
import tkinter as tk
from tkinter import filedialog, ttk

from constants import LABEL_WIDTH


class FolderPicker(ttk.Frame):
    """Lets the user pick (or type) the source folder."""

    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self.path_var = tk.StringVar()

        ttk.Label(self, text="Folder:", width=LABEL_WIDTH, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Entry(self, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self.browse_button = ttk.Button(self, text="Browse…", command=self._browse)
        self.browse_button.pack(side=tk.LEFT)

    def _browse(self):
        folder = filedialog.askdirectory(title="Pick a folder to upload from")
        if folder:
            self.set(os.path.normpath(folder))

    def get(self):
        return self.path_var.get().strip()

    def set(self, value):
        self.path_var.set(value)
        if self.on_change:
            self.on_change()

    def set_busy(self, busy):
        self.browse_button.config(state=tk.DISABLED if busy else tk.NORMAL)

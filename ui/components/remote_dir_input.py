"""Remote directory input row: label + entry + hint."""

import tkinter as tk
from tkinter import ttk

from constants import LABEL_WIDTH


class RemoteDirInput(ttk.Frame):
    """Name of the folder inside the storage zone (empty = zone root)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.dir_var = tk.StringVar()

        ttk.Label(self, text="Remote dir:", width=LABEL_WIDTH, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Entry(self, textvariable=self.dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Label(self, text="empty = zone root", foreground="#888").pack(side=tk.LEFT)

    def get(self):
        return self.dir_var.get().strip()

"""Determinate progress bar for the upload run."""

import tkinter as tk
from tkinter import ttk


class ProgressBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(self, variable=self.progress_var, maximum=100).pack(fill=tk.X, expand=True)

    def set(self, done, total):
        self.progress_var.set((done / total * 100) if total else 0)

    def reset(self):
        self.progress_var.set(0)

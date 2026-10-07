"""Bottom status bar: current operation (left) + API state (right)."""

import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var).pack(side=tk.LEFT)

        self.api_var = tk.StringVar(value="Checking API…")
        ttk.Label(self, textvariable=self.api_var, foreground="#666").pack(side=tk.RIGHT)

    def set_status(self, text):
        self.status_var.set(text)

    def set_api(self, text):
        self.api_var.set(text)

"""Colored log panel."""

import tkinter as tk
from tkinter import ttk

TAG_COLORS = {"ok": "#2e7d32", "fail": "#c62828", "info": "#555555"}


class LogPanel(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Log", padding=4)

        self.text = tk.Text(self, height=8, state=tk.DISABLED, wrap="word")
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.config(yscrollcommand=scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        for tag, color in TAG_COLORS.items():
            self.text.tag_configure(tag, foreground=color)

    def log(self, message, tag="info"):
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, message + "\n", tag)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)

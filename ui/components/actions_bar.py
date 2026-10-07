"""Actions row: Rescan / Upload / Stop buttons + scan summary."""

import tkinter as tk
from tkinter import ttk


class ActionsBar(ttk.Frame):
    """Buttons wired by the app; owns the busy-state and the scan summary."""

    def __init__(self, parent, on_rescan, on_upload, on_stop):
        super().__init__(parent)

        self.rescan_button = ttk.Button(self, text="Rescan", command=on_rescan)
        self.rescan_button.pack(side=tk.LEFT)

        self.upload_button = ttk.Button(self, text="Upload", command=on_upload)
        self.upload_button.pack(side=tk.LEFT, padx=8)

        self.stop_button = ttk.Button(self, text="Stop", command=on_stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        self.count_var = tk.StringVar(value="No files scanned yet.")
        ttk.Label(self, textvariable=self.count_var).pack(side=tk.RIGHT)

    def set_count(self, text):
        self.count_var.set(text)

    def set_busy(self, busy):
        state = tk.DISABLED if busy else tk.NORMAL
        self.rescan_button.config(state=state)
        self.upload_button.config(state=state)
        self.stop_button.config(state=tk.NORMAL if busy else tk.DISABLED)

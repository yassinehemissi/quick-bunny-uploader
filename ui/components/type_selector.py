"""File type selection: group checkboxes + custom extensions + hint label."""

import re
import tkinter as tk
from tkinter import ttk

from constants import LABEL_WIDTH, TYPE_GROUPS


class TypeSelector(ttk.Frame):
    """Checkbox per extension family, plus a free-form custom extensions field."""

    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self.type_vars = {}
        self.custom_var = tk.StringVar()

        ttk.Label(self, text="Types:", width=LABEL_WIDTH, anchor=tk.NW).pack(side=tk.LEFT, anchor=tk.NW)

        box = ttk.Frame(self)
        box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        for i, group in enumerate(TYPE_GROUPS):
            var = tk.BooleanVar(value=(group == "Images"))
            self.type_vars[group] = var
            ttk.Checkbutton(box, text=group, variable=var, command=self._changed).grid(
                row=i // 3, column=i % 3, sticky=tk.W, padx=(0, 18)
            )

        custom_row = ttk.Frame(box)
        custom_row.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(4, 0))
        ttk.Label(custom_row, text="Custom:").pack(side=tk.LEFT)
        custom_entry = ttk.Entry(custom_row, textvariable=self.custom_var, width=32)
        custom_entry.pack(side=tk.LEFT, padx=6)
        custom_entry.bind("<KeyRelease>", lambda _e: self._changed())
        ttk.Label(custom_row, text="(e.g. psd, ai, glb)", foreground="#888").pack(side=tk.LEFT)

        self.selected_var = tk.StringVar()
        ttk.Label(box, textvariable=self.selected_var, foreground="#666", wraplength=480, justify=tk.LEFT).grid(
            row=3, column=0, columnspan=3, sticky=tk.W, pady=(4, 0)
        )

        self._update_hint()

    def _changed(self):
        self._update_hint()
        if self.on_change:
            self.on_change()

    def selected_extensions(self):
        exts = set()
        for group, var in self.type_vars.items():
            if var.get():
                exts.update(TYPE_GROUPS[group])
        for token in re.split(r"[,\s]+", self.custom_var.get().lower()):
            token = token.strip().lstrip(".").strip()
            if token:
                exts.add(token)
        return exts

    def _update_hint(self):
        exts = sorted(self.selected_extensions())
        text = ", ".join(exts) if exts else "none — pick at least one type or custom extension"
        self.selected_var.set(f"Matching extensions: {text}")

"""
Quick Bunny Uploader — tiny tkinter UI.

Picks a local folder, filters its TOP-LEVEL files (no subfolders) by the
selected extensions, then uploads them one by one to Bunny CDN Storage via
the local Express API (api/server.js, normally started by run.py).
"""

import json
import os
import queue
import re
import threading
import urllib.error
import urllib.request

import tkinter as tk
from tkinter import END, filedialog, messagebox, ttk

API_URL = os.environ.get("BUNNY_API_URL", "http://127.0.0.1:3999")
UPLOAD_TIMEOUT = 600  # seconds without socket progress before one upload gives up

TYPE_GROUPS = {
    "Images": ("jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "avif", "ico", "tiff"),
    "Videos": ("mp4", "webm", "mov", "mkv", "avi", "m4v", "flv", "wmv"),
    "Audio": ("mp3", "wav", "ogg", "m4a", "flac", "aac", "opus"),
    "Documents": ("pdf", "doc", "docx", "txt", "md", "csv", "xls", "xlsx", "ppt", "pptx", "json", "xml"),
    "Archives": ("zip", "rar", "7z", "tar", "gz", "bz2"),
}


def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def api_health():
    try:
        with urllib.request.urlopen(f"{API_URL}/health", timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return f"API online — zone: {data.get('zone', '?')}"
    except Exception as err:
        return f"API offline ({err})"


def api_upload(file_path, remote_dir):
    """POST {path, dir} to the Express API. Always returns a dict, never raises."""
    body = json.dumps({"path": file_path, "dir": remote_dir}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}/upload",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=UPLOAD_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", "replace")
        try:
            data = json.loads(raw)
            return {"ok": False, "error": data.get("error") or data.get("message") or f"HTTP {err.code}"}
        except ValueError:
            return {"ok": False, "error": f"HTTP {err.code}: {raw[:200] or err.reason}"}


class App:
    def __init__(self, root):
        self.root = root
        root.title("Quick Bunny Uploader")
        root.minsize(620, 560)

        self.q = queue.Queue()
        self.matches = []  # [(full_path, file_name, size_bytes)]
        self.stop_event = threading.Event()
        self.worker = None

        self._build_ui()
        self._update_selected_label()
        threading.Thread(target=self._probe_api, daemon=True).start()

        root.protocol("WM_DELETE_WINDOW", self._on_close)
        root.after(100, self._poll_queue)

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(1, weight=1)

        # Folder picker
        ttk.Label(outer, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.folder_var = tk.StringVar()
        ttk.Entry(outer, textvariable=self.folder_var).grid(row=0, column=1, sticky=tk.EW, padx=8)
        self.browse_btn = ttk.Button(outer, text="Browse…", command=self.pick_folder)
        self.browse_btn.grid(row=0, column=2, sticky=tk.EW)

        # Remote directory name
        ttk.Label(outer, text="Remote dir:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.dir_var = tk.StringVar()
        ttk.Entry(outer, textvariable=self.dir_var).grid(row=1, column=1, sticky=tk.EW, padx=8)
        ttk.Label(outer, text="empty = zone root", foreground="#888").grid(row=1, column=2)

        # File types
        ttk.Label(outer, text="Types:").grid(row=2, column=0, sticky=tk.NW, pady=3)
        types = ttk.Frame(outer)
        types.grid(row=2, column=1, sticky=tk.EW, padx=8)
        self.type_vars = {}
        for i, group in enumerate(TYPE_GROUPS):
            var = tk.BooleanVar(value=(group == "Images"))
            self.type_vars[group] = var
            ttk.Checkbutton(types, text=group, variable=var, command=self._types_changed).grid(
                row=i // 3, column=i % 3, sticky=tk.W, padx=(0, 18)
            )
        custom_row = ttk.Frame(types)
        custom_row.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(4, 0))
        ttk.Label(custom_row, text="Custom:").pack(side=tk.LEFT)
        self.custom_var = tk.StringVar()
        custom_entry = ttk.Entry(custom_row, textvariable=self.custom_var, width=32)
        custom_entry.pack(side=tk.LEFT, padx=6)
        custom_entry.bind("<KeyRelease>", lambda _e: self._types_changed())
        ttk.Label(custom_row, text="(e.g. psd, ai, glb)", foreground="#888").pack(side=tk.LEFT)

        self.selected_var = tk.StringVar()
        ttk.Label(
            outer, textvariable=self.selected_var, foreground="#666", wraplength=480, justify=tk.LEFT
        ).grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=8)

        # Actions
        actions = ttk.Frame(outer)
        actions.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=(10, 4))
        self.scan_btn = ttk.Button(actions, text="Rescan", command=self.scan_clicked)
        self.scan_btn.pack(side=tk.LEFT)
        self.upload_btn = ttk.Button(actions, text="Upload", command=self.start_upload)
        self.upload_btn.pack(side=tk.LEFT, padx=8)
        self.stop_btn = ttk.Button(actions, text="Stop", command=self.stop_upload, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        self.count_var = tk.StringVar(value="No files scanned yet.")
        ttk.Label(actions, textvariable=self.count_var).pack(side=tk.RIGHT)

        # Progress
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(outer, variable=self.progress_var, maximum=100).grid(
            row=5, column=0, columnspan=3, sticky=tk.EW, pady=(2, 6)
        )

        # Matched files
        files = ttk.LabelFrame(outer, text="Matched files (top level only)", padding=4)
        files.grid(row=6, column=0, columnspan=3, sticky=tk.NSEW)
        self.file_listbox = tk.Listbox(files, height=7)
        files_scroll = ttk.Scrollbar(files, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=files_scroll.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Log
        logf = ttk.LabelFrame(outer, text="Log", padding=4)
        logf.grid(row=7, column=0, columnspan=3, sticky=tk.NSEW, pady=(8, 0))
        self.log_text = tk.Text(logf, height=8, state=tk.DISABLED, wrap="word")
        log_scroll = ttk.Scrollbar(logf, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        for tag, color in (("ok", "#2e7d32"), ("fail", "#c62828"), ("info", "#555555")):
            self.log_text.tag_configure(tag, foreground=color)

        # Status bar
        bottom = ttk.Frame(outer)
        bottom.grid(row=8, column=0, columnspan=3, sticky=tk.EW, pady=(8, 0))
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(bottom, textvariable=self.status_var).pack(side=tk.LEFT)
        self.api_var = tk.StringVar(value="Checking API…")
        ttk.Label(bottom, textvariable=self.api_var, foreground="#666").pack(side=tk.RIGHT)

        outer.rowconfigure(6, weight=2)
        outer.rowconfigure(7, weight=3)

    # ------------------------------------------------------- folder & scan

    def pick_folder(self):
        folder = filedialog.askdirectory(title="Pick a folder to upload from")
        if folder:
            self.folder_var.set(os.path.normpath(folder))
            self.scan_folder(verbose=True)

    def scan_clicked(self):
        self.scan_folder(verbose=True)

    def _types_changed(self):
        self._update_selected_label()
        if self.folder_var.get().strip() and not self._busy():
            self.scan_folder(verbose=False)

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

    def _update_selected_label(self):
        exts = sorted(self.selected_extensions())
        text = ", ".join(exts) if exts else "none — pick at least one type or custom extension"
        self.selected_var.set(f"Matching extensions: {text}")

    def scan_folder(self, verbose=False):
        folder = self.folder_var.get().strip()
        if not folder:
            if verbose:
                messagebox.showwarning("No folder", "Pick a folder first.", parent=self.root)
            return
        exts = self.selected_extensions()
        if not exts:
            if verbose:
                messagebox.showwarning("No file types", "Select at least one file type.", parent=self.root)
            return

        matches = []
        try:
            with os.scandir(folder) as entries:
                for entry in entries:  # top level only, never recursive
                    if entry.is_file() and os.path.splitext(entry.name)[1].lstrip(".").lower() in exts:
                        matches.append((entry.path, entry.name, entry.stat().st_size))
        except OSError as err:
            if verbose:
                messagebox.showerror("Scan failed", str(err), parent=self.root)
            return

        matches.sort(key=lambda m: m[1].lower())
        self.matches = matches
        self.file_listbox.delete(0, END)
        for _path, name, size in matches:
            self.file_listbox.insert(END, f"{name}  —  {human_size(size)}")
        total = sum(m[2] for m in matches)
        self.count_var.set(f"{len(matches)} file(s), {human_size(total)}" if matches else "No matching files.")
        self.status_var.set(f"Scanned: {len(matches)} file(s) matched.")

    # --------------------------------------------------------------- upload

    def _busy(self):
        return self.worker is not None and self.worker.is_alive()

    def start_upload(self):
        if self._busy():
            return
        if not self.matches:
            messagebox.showwarning(
                "Nothing to upload", "Scan a folder with matching files first.", parent=self.root
            )
            return

        files = list(self.matches)
        remote_dir = self.dir_var.get().strip()
        self.stop_event.clear()
        self._clear_log()
        self._set_busy(True)
        self.progress_var.set(0)
        self._log(f"Uploading {len(files)} file(s) → '{remote_dir or 'zone root'}'", "info")
        self.worker = threading.Thread(target=self._upload_worker, args=(files, remote_dir), daemon=True)
        self.worker.start()

    def stop_upload(self):
        self.stop_event.set()
        self._log("Stopping after the current file…", "info")

    def _upload_worker(self, files, remote_dir):
        total = len(files)
        ok = fail = 0
        for i, (file_path, name, _size) in enumerate(files, start=1):
            if self.stop_event.is_set():
                break
            self.q.put(("progress", i - 1, total, f"[{i}/{total}] {name}"))
            self._log_threadsafe(f"[{i}/{total}] {name}")
            try:
                result = api_upload(file_path, remote_dir)
            except Exception as err:  # UI must survive any API failure
                result = {"ok": False, "error": str(err)}

            if result.get("ok"):
                ok += 1
                where = result.get("publicUrl") or result.get("remotePath") or ""
                self._log_threadsafe(f"    ok ({result.get('status')}) — {where}", "ok")
                self.q.put(("progress", i, total, f"[{i}/{total}] {name} — ok"))
            else:
                fail += 1
                why = result.get("error") or result.get("message") or f"HTTP {result.get('status')}"
                self._log_threadsafe(f"    failed — {why}", "fail")
                self.q.put(("progress", i, total, f"[{i}/{total}] {name} — failed"))

        stopped = self.stop_event.is_set() and ok + fail < total
        self.q.put(("finished", ok, fail, stopped))

    def _log_threadsafe(self, text, tag="info"):
        self.q.put(("log", text, tag))

    # ------------------------------------------------------- queue → widgets

    def _probe_api(self):
        self.q.put(("api", api_health()))

    def _poll_queue(self):
        try:
            while True:
                kind, *rest = self.q.get_nowait()
                if kind == "log":
                    self._log(rest[0], rest[1] if len(rest) > 1 else "info")
                elif kind == "progress":
                    done, total, text = rest
                    self.progress_var.set((done / total * 100) if total else 0)
                    self.status_var.set(text)
                elif kind == "busy":
                    self._set_busy(rest[0])
                elif kind == "finished":
                    self._on_finished(rest[0], rest[1], rest[2])
                elif kind == "api":
                    self.api_var.set(rest[0])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _on_finished(self, ok, fail, stopped):
        summary = f"{'Stopped' if stopped else 'Done'} — {ok} uploaded, {fail} failed."
        self._log(summary, "fail" if (fail or stopped) else "ok")
        self.status_var.set(summary)
        self._set_busy(False)

    def _set_busy(self, busy):
        self.upload_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
        self.scan_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
        self.browse_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL if busy else tk.DISABLED)

    # ------------------------------------------------------------- log utils

    def _log(self, text, tag="info"):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(END, text + "\n", tag)
        self.log_text.see(END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", END)
        self.log_text.config(state=tk.DISABLED)

    def _on_close(self):
        self.stop_event.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

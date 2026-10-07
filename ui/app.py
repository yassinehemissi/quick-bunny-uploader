"""
Quick Bunny Uploader — tiny tkinter UI (composition root).

Wires the components in ui/components/ to the services in ui/services/:
picking a folder, filtering its top-level files by extension, then uploading
them one by one to Bunny CDN Storage through the local Express API
(api/server.js, normally started by run.py).
"""

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from components.actions_bar import ActionsBar
from components.file_list import FileList
from components.folder_picker import FolderPicker
from components.log_panel import LogPanel
from components.progress import ProgressBar
from components.remote_dir_input import RemoteDirInput
from components.status_bar import StatusBar
from components.type_selector import TypeSelector
from services.api_client import api_health
from services.scanner import scan_folder
from services.uploader import UploadWorker
from utils import human_size


class App:
    def __init__(self, root):
        self.root = root
        root.title("Quick Bunny Uploader")
        root.minsize(620, 560)

        self.events = queue.Queue()
        self.matches = []  # [(full_path, file_name, size_bytes)]
        self.stop_event = threading.Event()
        self.worker = None

        self._build()
        threading.Thread(target=self._probe_api, daemon=True).start()
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        root.after(100, self._pump_events)

    # ----------------------------------------------------------------- layout

    def _build(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        self.folder_picker = FolderPicker(outer, on_change=self._auto_rescan)
        self.remote_dir = RemoteDirInput(outer)
        self.type_selector = TypeSelector(outer, on_change=self._auto_rescan)
        self.actions = ActionsBar(
            outer, on_rescan=self.rescan_clicked, on_upload=self.start_upload, on_stop=self.stop_upload
        )
        self.progress = ProgressBar(outer)
        self.file_list = FileList(outer)
        self.log_panel = LogPanel(outer)
        self.status_bar = StatusBar(outer)

        self.folder_picker.grid(row=0, column=0, sticky=tk.EW, pady=3)
        self.remote_dir.grid(row=1, column=0, sticky=tk.EW, pady=3)
        self.type_selector.grid(row=2, column=0, sticky=tk.EW, pady=3)
        self.actions.grid(row=3, column=0, sticky=tk.EW, pady=(10, 4))
        self.progress.grid(row=4, column=0, sticky=tk.EW, pady=(2, 6))
        self.file_list.grid(row=5, column=0, sticky=tk.NSEW)
        self.log_panel.grid(row=6, column=0, sticky=tk.NSEW, pady=(8, 0))
        self.status_bar.grid(row=7, column=0, sticky=tk.EW, pady=(8, 0))

        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(5, weight=2)
        outer.rowconfigure(6, weight=3)

    # ----------------------------------------------------------- scan actions

    def _auto_rescan(self):
        if not self._busy():
            self.rescan(verbose=False)

    def rescan_clicked(self):
        self.rescan(verbose=True)

    def rescan(self, verbose=False):
        folder = self.folder_picker.get()
        if not folder:
            if verbose:
                messagebox.showwarning("No folder", "Pick a folder first.", parent=self.root)
            return
        extensions = self.type_selector.selected_extensions()
        if not extensions:
            if verbose:
                messagebox.showwarning("No file types", "Select at least one file type.", parent=self.root)
            return
        try:
            self.matches = scan_folder(folder, extensions)
        except OSError as err:
            if verbose:
                messagebox.showerror("Scan failed", str(err), parent=self.root)
            return

        self.file_list.set_files(self.matches)
        total = sum(m[2] for m in self.matches)
        count_text = f"{len(self.matches)} file(s), {human_size(total)}" if self.matches else "No matching files."
        self.actions.set_count(count_text)
        self.status_bar.set_status(f"Scanned: {len(self.matches)} file(s) matched.")

    # --------------------------------------------------------- upload actions

    def start_upload(self):
        if self._busy():
            return
        if not self.matches:
            messagebox.showwarning("Nothing to upload", "Scan a folder with matching files first.", parent=self.root)
            return

        remote_dir = self.remote_dir.get()
        self.stop_event.clear()
        self.log_panel.clear()
        self.progress.reset()
        self._set_busy(True)
        self.log_panel.log(f"Uploading {len(self.matches)} file(s) → '{remote_dir or 'zone root'}'")
        self.worker = UploadWorker(list(self.matches), remote_dir, self.events, self.stop_event)
        self.worker.start()

    def stop_upload(self):
        self.stop_event.set()
        self.log_panel.log("Stopping after the current file…")

    def _set_busy(self, busy):
        self.actions.set_busy(busy)
        self.folder_picker.set_busy(busy)

    def _busy(self):
        return self.worker is not None and self.worker.is_alive()

    # ------------------------------------------------------ events from worker

    def _probe_api(self):
        self.events.put(("api", api_health()))

    def _pump_events(self):
        try:
            while True:
                kind, *rest = self.events.get_nowait()
                if kind == "log":
                    self.log_panel.log(rest[0], rest[1] if len(rest) > 1 else "info")
                elif kind == "progress":
                    done, total, text = rest
                    self.progress.set(done, total)
                    self.status_bar.set_status(text)
                elif kind == "finished":
                    ok, fail, stopped = rest
                    summary = f"{'Stopped' if stopped else 'Done'} — {ok} uploaded, {fail} failed."
                    self.log_panel.log(summary, "fail" if (fail or stopped) else "ok")
                    self.status_bar.set_status(summary)
                    self._set_busy(False)
                elif kind == "api":
                    self.status_bar.set_api(rest[0])
        except queue.Empty:
            pass
        self.root.after(100, self._pump_events)

    def _on_close(self):
        self.stop_event.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

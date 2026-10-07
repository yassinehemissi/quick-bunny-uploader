"""Background worker that uploads files one by one via the API client."""

import threading

from services.api_client import api_upload


class UploadWorker(threading.Thread):
    """Uploads `files` sequentially, reporting progress through `events` (a queue.Queue).

    Event tuples put on the queue:
        ("log", text, tag)          — log line ("ok" | "fail" | "info")
        ("progress", done, total, status_text)
        ("finished", ok, fail, stopped)
    """

    def __init__(self, files, remote_dir, events, stop_event):
        super().__init__(daemon=True)
        self.files = files  # [(full_path, file_name, size_bytes)]
        self.remote_dir = remote_dir
        self.events = events
        self.stop_event = stop_event

    def run(self):
        total = len(self.files)
        ok = fail = 0
        for i, (file_path, name, _size) in enumerate(self.files, start=1):
            if self.stop_event.is_set():
                break
            self._report("progress", i - 1, total, f"[{i}/{total}] {name}")
            self._report("log", f"[{i}/{total}] {name}", "info")

            try:
                result = api_upload(file_path, self.remote_dir)
            except Exception as err:  # the UI must survive any API failure
                result = {"ok": False, "error": str(err)}

            if result.get("ok"):
                ok += 1
                where = result.get("publicUrl") or result.get("remotePath") or ""
                self._report("log", f"    ok ({result.get('status')}) — {where}", "ok")
                self._report("progress", i, total, f"[{i}/{total}] {name} — ok")
            else:
                fail += 1
                why = result.get("error") or result.get("message") or f"HTTP {result.get('status')}"
                self._report("log", f"    failed — {why}", "fail")
                self._report("progress", i, total, f"[{i}/{total}] {name} — failed")

        stopped = self.stop_event.is_set() and ok + fail < total
        self._report("finished", ok, fail, stopped)

    def _report(self, *event):
        self.events.put(event)

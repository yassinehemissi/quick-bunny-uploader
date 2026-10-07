"""HTTP client for the local Express upload API."""

import json
import urllib.error
import urllib.request

from constants import API_URL, UPLOAD_TIMEOUT


def api_health():
    """Return a human-readable API status string."""
    try:
        with urllib.request.urlopen(f"{API_URL}/health", timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return f"API online — zone: {data.get('zone', '?')}"
    except Exception as err:
        return f"API offline ({err})"


def api_upload(file_path, remote_dir):
    """POST {path, dir} to the API. Always returns a dict, never raises."""
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

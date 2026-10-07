"""
Quick Bunny Uploader — launcher.

Starts the Express upload API (api/server.js), waits for it to be healthy,
then launches the tkinter UI (ui/app.py). When the UI window closes, the API
is stopped too.

Usage:
    python run.py
"""

import atexit
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
API_DIR = os.path.join(ROOT, "api")
DEFAULT_PORT = "3999"

api_proc = None
ui_proc = None


def resolve_port():
    """BUNNY_API_PORT env > port in api/config.json > default."""
    if os.environ.get("BUNNY_API_PORT"):
        return os.environ["BUNNY_API_PORT"]
    try:
        with open(os.path.join(API_DIR, "config.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        if cfg.get("port"):
            return str(cfg["port"])
    except (OSError, ValueError):
        pass
    return DEFAULT_PORT


def api_url():
    return f"http://127.0.0.1:{resolve_port()}"


def api_healthy(timeout=1):
    try:
        with urllib.request.urlopen(f"{api_url()}/health", timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def stop(proc):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def cleanup():
    global api_proc, ui_proc
    stop(ui_proc)
    stop(api_proc)


def main():
    global api_proc, ui_proc

    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node or not npm:
        sys.exit("Node.js and npm are required. Install them from https://nodejs.org")

    if not os.path.isfile(os.path.join(API_DIR, "config.json")):
        print("NOTE: api/config.json not found.")
        print("      Copy api/config.example.json to api/config.json and add your Bunny")
        print("      Storage Zone + Access Key, otherwise the API will refuse to start.\n")

    if not os.path.isdir(os.path.join(API_DIR, "node_modules")):
        print("Installing API dependencies (first run only)...")
        result = subprocess.run([npm, "install"], cwd=API_DIR)
        if result.returncode != 0:
            sys.exit("npm install failed — see output above.")

    print(f"Starting upload API on {api_url()} ...")
    api_proc = subprocess.Popen(
        [node, "server.js"],
        cwd=API_DIR,
        env=dict(os.environ, BUNNY_API_PORT=resolve_port()),
    )

    for _ in range(50):  # up to ~10 seconds
        if api_proc.poll() is not None:
            sys.exit(
                "API exited immediately — check Bunny credentials in api/config.json,\n"
                "or run 'npm install' inside api/ if a module was reported missing."
            )
        if api_healthy():
            break
        time.sleep(0.2)
    else:
        cleanup()
        sys.exit("API did not come up in time (10s).")

    print("API is up. Launching UI...")
    ui_proc = subprocess.Popen(
        [sys.executable, os.path.join("ui", "app.py")],
        cwd=ROOT,
        env=dict(os.environ, BUNNY_API_URL=api_url()),
    )

    try:
        code = ui_proc.wait()
        if code != 0:
            print(f"UI exited with code {code} — if it flashed an error, try: python ui/app.py")
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
        print("Stopped API and UI. Bye!")


if __name__ == "__main__":
    atexit.register(cleanup)
    main()

# Quick Bunny Uploader 🐰

Personal, lightweight tool: pick a local folder, choose file types, and upload the
folder's top-level files **one by one** to **Bunny CDN Storage** through a tiny
local Express API. Not production stuff — just a handy personal utility.

## What's inside

```
run.py                  starts the API, then the UI; stops both when the UI closes
api/server.js           Express API — streams each file to Bunny Storage
api/config.example.json copy to api/config.json and fill in your Bunny credentials
ui/app.py               tkinter UI — folder picker, remote dir, file types, upload log
```

## One-time setup

1. Install [Node.js](https://nodejs.org) (18+). Python 3.8+ (with tkinter) is enough for the rest.
2. Copy `api/config.example.json` to `api/config.json` and fill it in:
   - `storageZone` — the storage zone name from the Bunny dashboard
   - `accessKey` — the zone's **Access Key** (Bunny dashboard → Storage → your zone → *FTP & API Access*)
   - `publicHost` *(optional)* — e.g. `myzone.b-cdn.net`, used to show public links after upload
   - `port` *(optional, default 3999)*
3. Install API dependencies: `cd api && npm install`
   (`run.py` does this automatically on first run)

## Run

```
python run.py
```

- The API listens on `http://127.0.0.1:3999` (localhost only). Override with `BUNNY_API_PORT` or `port` in config.json.
- The UI receives the API URL automatically from `run.py` (or set `BUNNY_API_URL` yourself).

## UI in one glance

- **Folder** — source folder; only its **top-level files** are used (no subfolders, not recursive)
- **Remote dir** — folder name inside the storage zone; leave empty for the zone root;
  existing files with the same name are overwritten
- **Types** — checkboxes per family, plus a custom extension field (e.g. `psd, ai, glb`)
- Files upload sequentially (one at a time); **Stop** cancels after the current file

## Notes

- `api/config.json` is gitignored — never commit your access key.
- The API accepts local file paths and is bound to `127.0.0.1` on purpose. Don't expose it.
- Credentials can also come from env vars: `BUNNY_STORAGE_ZONE`, `BUNNY_ACCESS_KEY`,
  `BUNNY_PUBLIC_HOST`, `BUNNY_API_PORT`.

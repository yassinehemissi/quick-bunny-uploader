# Quick Bunny Uploader 🐰

Personal, lightweight tool: pick a local folder, choose file types, and upload the
folder's top-level files **one by one** to **Bunny CDN Storage** through a tiny
local Express API. Not production stuff — just a handy personal utility.

## What's inside

```
run.py                     starts the API, then the UI; stops both when the UI closes

api/
  server.js                entry point — creates the app, listens on localhost only
  src/app.js               middleware + routers
  src/config.js            Bunny credentials + port (api/config.json or env vars)
  src/bunny.js             Bunny Storage helpers (path sanitizing, streamed PUT)
  src/format.js            log formatting helpers
  src/routes/health.js     GET  /health — readiness probe
  src/routes/upload.js     POST /upload — streams one local file to Bunny Storage
  config.example.json      copy to api/config.json and fill in your Bunny credentials

ui/
  app.py                   composition root — wires components to services
  constants.py             shared constants (API URL, file type groups, …)
  utils.py                 small shared helpers
  components/               one self-contained widget per module
    folder_picker.py       folder row: path entry + Browse…
    remote_dir_input.py    remote directory name row
    type_selector.py       file type checkboxes + custom extensions
    actions_bar.py         Rescan / Upload / Stop + scan summary
    progress.py            upload progress bar
    file_list.py           matched files listbox
    log_panel.py           colored log
    status_bar.py          current operation + API status
  services/
    api_client.py          HTTP client for the Express API
    scanner.py             top-level folder scanner
    uploader.py            background worker — uploads one file at a time
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

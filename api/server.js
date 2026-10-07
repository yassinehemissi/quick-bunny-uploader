/**
 * Quick Bunny Uploader — tiny local Express API.
 *
 * Endpoints:
 *   GET  /health  -> { ok: true, zone }
 *   POST /upload  -> body: { path: "local file path", dir: "remote dir (optional)" }
 *                    streams the file to Bunny Storage as {zone}/{dir}/{file},
 *                    one file per request. Sequential uploading is the client's job.
 *
 * Config: api/config.json (see config.example.json) or env vars:
 *   BUNNY_STORAGE_ZONE, BUNNY_ACCESS_KEY, BUNNY_PUBLIC_HOST, BUNNY_API_PORT
 *
 * Localhost-only on purpose — this is a personal tool, not a public service.
 */

const express = require("express");
const fs = require("fs");
const https = require("https");
const path = require("path");

const BUNNY_STORAGE_URL = "https://storage.bunnycdn.com";
const CONFIG_PATH = path.join(__dirname, "config.json");

// ---- config -----------------------------------------------------------------

function loadConfig() {
  let fileConfig = {};
  if (fs.existsSync(CONFIG_PATH)) {
    try {
      fileConfig = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
    } catch (err) {
      console.error(`[config] api/config.json is not valid JSON: ${err.message}`);
      process.exit(1);
    }
  }

  const config = {
    storageZone: process.env.BUNNY_STORAGE_ZONE || fileConfig.storageZone,
    accessKey: process.env.BUNNY_ACCESS_KEY || fileConfig.accessKey,
    publicHost: (process.env.BUNNY_PUBLIC_HOST || fileConfig.publicHost || "").replace(/^https?:\/\//, ""),
    port: Number(process.env.BUNNY_API_PORT || fileConfig.port || 3999),
  };

  const missing = ["storageZone", "accessKey"].filter((key) => !config[key]);
  if (missing.length) {
    console.error(
      `[config] Missing Bunny ${missing.join(" and ")}. ` +
        "Copy api/config.example.json to api/config.json and fill it in."
    );
    process.exit(1);
  }
  return config;
}

const config = loadConfig();

// ---- helpers ----------------------------------------------------------------

function sanitizeRemoteDir(dir) {
  if (!dir) return "";
  return String(dir)
    .replace(/\\/g, "/")
    .split("/")
    .map((part) => part.trim())
    .filter((part) => part && part !== "." && part !== "..")
    .join("/");
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let size = bytes / 1024;
  let i = 0;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i += 1;
  }
  return `${size.toFixed(1)} ${units[i]}`;
}

function putToBunny(url, filePath, size) {
  // Streams the file straight from disk to Bunny (no full-file buffering).
  return new Promise((resolve, reject) => {
    const request = https.request(
      url,
      {
        method: "PUT",
        headers: { AccessKey: config.accessKey, "Content-Length": size },
      },
      (res) => {
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => resolve({ status: res.statusCode, body }));
      }
    );
    request.setTimeout(120000, () => request.destroy(new Error("Bunny request timed out (no progress for 120s)")));
    request.on("error", reject);
    fs.createReadStream(filePath).on("error", reject).pipe(request);
  });
}

// ---- app ----------------------------------------------------------------------

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "1mb" }));

app.get("/health", (_req, res) => {
  res.json({ ok: true, zone: config.storageZone });
});

app.post("/upload", async (req, res) => {
  const filePath = req.body && req.body.path;
  const remoteDir = sanitizeRemoteDir(req.body && req.body.dir);

  if (typeof filePath !== "string" || !filePath.trim()) {
    return res.status(400).json({ ok: false, error: "Missing 'path' in request body." });
  }

  let stat;
  try {
    stat = fs.statSync(filePath);
  } catch {
    return res.status(404).json({ ok: false, error: `File not found: ${filePath}` });
  }
  if (!stat.isFile()) {
    return res.status(400).json({ ok: false, error: `Not a file: ${filePath}` });
  }

  const fileName = path.basename(filePath);
  const segments = remoteDir ? [...remoteDir.split("/"), fileName] : [fileName];
  const remotePath = segments.map(encodeURIComponent).join("/");
  const uploadUrl = `${BUNNY_STORAGE_URL}/${encodeURIComponent(config.storageZone)}/${remotePath}`;

  console.log(`[upload] ${fileName} (${formatSize(stat.size)}) -> ${remoteDir || "(zone root)"}`);

  try {
    const result = await putToBunny(uploadUrl, filePath, stat.size);
    const ok = result.status >= 200 && result.status < 300;
    console.log(`[upload] ${fileName} -> HTTP ${result.status} ${ok ? "OK" : "FAILED"}`);
    res.status(ok ? 200 : 502).json({
      ok,
      status: result.status,
      file: fileName,
      remotePath: `${config.storageZone}/${segments.join("/")}`,
      publicUrl: config.publicHost ? `https://${config.publicHost}/${remotePath}` : null,
      message: ok
        ? "Uploaded."
        : `Bunny returned HTTP ${result.status}${result.body ? `: ${String(result.body).slice(0, 200)}` : ""}`,
    });
  } catch (err) {
    console.error(`[upload] ${fileName} -> ERROR: ${err.message}`);
    res.status(502).json({ ok: false, file: fileName, error: err.message });
  }
});

// anything else -> plain 404
app.use((_req, res) => res.status(404).json({ ok: false, error: "Unknown route." }));

app.listen(config.port, "127.0.0.1", () => {
  console.log(`[api] Quick Bunny Uploader API listening on http://127.0.0.1:${config.port}`);
  console.log(
    `[api] Bunny storage zone: ${config.storageZone}` +
      (config.publicHost ? ` (public: https://${config.publicHost})` : "")
  );
});

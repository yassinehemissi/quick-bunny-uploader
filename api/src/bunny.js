/** Bunny CDN Storage helpers: path sanitizing + streamed PUT uploads. */

const fs = require("fs");
const https = require("https");

const config = require("./config");

const STORAGE_URL = "https://storage.bunnycdn.com";
const REQUEST_TIMEOUT_MS = 120000; // aborts if no socket progress for 2 minutes

function sanitizeRemoteDir(dir) {
  if (!dir) return "";
  return String(dir)
    .replace(/\\/g, "/")
    .split("/")
    .map((part) => part.trim())
    .filter((part) => part && part !== "." && part !== "..")
    .join("/");
}

function buildRemotePath(fileName, remoteDir) {
  const segments = remoteDir ? [...remoteDir.split("/"), fileName] : [fileName];
  return segments.map(encodeURIComponent).join("/");
}

function uploadUrlFor(remotePath) {
  return `${STORAGE_URL}/${encodeURIComponent(config.storageZone)}/${remotePath}`;
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
    request.setTimeout(REQUEST_TIMEOUT_MS, () =>
      request.destroy(new Error(`Bunny request timed out (no progress for ${REQUEST_TIMEOUT_MS / 1000}s)`))
    );
    request.on("error", reject);
    fs.createReadStream(filePath).on("error", reject).pipe(request);
  });
}

module.exports = { sanitizeRemoteDir, buildRemotePath, uploadUrlFor, putToBunny };

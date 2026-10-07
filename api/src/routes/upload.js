/**
 * POST /upload — body: { path: "local file path", dir: "remote dir (optional)" }
 * Streams one local file to Bunny Storage as {zone}/{dir}/{file}.
 */

const express = require("express");
const fs = require("fs");
const path = require("path");

const config = require("../config");
const { sanitizeRemoteDir, buildRemotePath, uploadUrlFor, putToBunny } = require("../bunny");
const { formatSize } = require("../format");

const router = express.Router();

router.post("/upload", async (req, res) => {
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
  const remotePath = buildRemotePath(fileName, remoteDir); // encoded, for URLs
  const uploadUrl = uploadUrlFor(remotePath);

  console.log(`[upload] ${fileName} (${formatSize(stat.size)}) -> ${remoteDir || "(zone root)"}`);

  try {
    const result = await putToBunny(uploadUrl, filePath, stat.size);
    const ok = result.status >= 200 && result.status < 300;
    console.log(`[upload] ${fileName} -> HTTP ${result.status} ${ok ? "OK" : "FAILED"}`);
    res.status(ok ? 200 : 502).json({
      ok,
      status: result.status,
      file: fileName,
      remotePath: `${config.storageZone}/${decodeURIComponent(remotePath)}`,
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

module.exports = router;

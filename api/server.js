/**
 * Quick Bunny Uploader — tiny local Express API (entry point).
 *
 * App pieces live in src/:
 *   src/app.js        middleware + routers
 *   src/config.js      Bunny credentials + port (api/config.json or env vars)
 *   src/bunny.js      Bunny Storage helpers (path sanitizing, streamed PUT)
 *   src/format.js     log formatting helpers
 *   src/routes/       one file per endpoint
 *
 * Localhost-only on purpose — this is a personal tool, not a public service.
 */

const config = require("./src/config");
const createApp = require("./src/app");

const app = createApp();

app.listen(config.port, "127.0.0.1", () => {
  console.log(`[api] Quick Bunny Uploader API listening on http://127.0.0.1:${config.port}`);
  console.log(
    `[api] Bunny storage zone: ${config.storageZone}` +
      (config.publicHost ? ` (public: https://${config.publicHost})` : "")
  );
});

/** Express app assembly: middleware + routers. */

const express = require("express");

const healthRouter = require("./routes/health");
const uploadRouter = require("./routes/upload");

function createApp() {
  const app = express();

  app.disable("x-powered-by");
  app.use(express.json({ limit: "1mb" }));

  app.use(healthRouter);
  app.use(uploadRouter);

  // anything else -> plain 404
  app.use((_req, res) => res.status(404).json({ ok: false, error: "Unknown route." }));

  return app;
}

module.exports = createApp;

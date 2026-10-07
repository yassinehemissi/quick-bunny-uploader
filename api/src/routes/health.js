/** GET /health — readiness probe used by run.py and the UI. */

const express = require("express");

const config = require("../config");

const router = express.Router();

router.get("/health", (_req, res) => {
  res.json({ ok: true, zone: config.storageZone });
});

module.exports = router;

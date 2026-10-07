/** Loads Bunny credentials + port from api/config.json or environment variables. */

const fs = require("fs");
const path = require("path");

const CONFIG_PATH = path.join(__dirname, "..", "config.json");

function readConfigFile() {
  if (!fs.existsSync(CONFIG_PATH)) return {};
  try {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
  } catch (err) {
    console.error(`[config] api/config.json is not valid JSON: ${err.message}`);
    process.exit(1);
  }
}

function loadConfig() {
  const fileConfig = readConfigFile();

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

module.exports = loadConfig();

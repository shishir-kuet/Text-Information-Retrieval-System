function logInfo(msg) {
  console.log(`[INFO] ${new Date().toISOString()} - ${msg}`);
}

function logError(msg, error = null) {
  console.error(`[ERROR] ${new Date().toISOString()} - ${msg}`);
  if (error) console.error(error);
}

function logWarn(msg) {
  console.warn(`[WARN] ${new Date().toISOString()} - ${msg}`);
}

// Export with both naming conventions for compatibility
module.exports = {
  logInfo,
  logError,
  logWarn,
  info: logInfo,
  error: logError,
  warn: logWarn
};

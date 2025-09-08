const fs = require('fs').promises;
const path = require('path');
const { ensureDirectoryExists } = require('./helpers');

const LOG_DIR = path.join(__dirname, '../../logs');
const LOG_FILE = path.join(LOG_DIR, 'radar-smr.log');

async function logMessage(level, message, metadata = {}) {
  try {
    await ensureDirectoryExists(LOG_DIR);
    
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      metadata
    };
    
    const logLine = JSON.stringify(logEntry) + '\n';
    await fs.appendFile(LOG_FILE, logLine);
  } catch (error) {
    console.error('Error writing to log file:', error);
  }
}

function info(message, metadata = {}) {
  console.log(`[INFO] ${message}`);
  logMessage('INFO', message, metadata);
}

function warn(message, metadata = {}) {
  console.warn(`[WARN] ${message}`);
  logMessage('WARN', message, metadata);
}

function error(message, metadata = {}) {
  console.error(`[ERROR] ${message}`);
  logMessage('ERROR', message, metadata);
}

function debug(message, metadata = {}) {
  if (process.env.NODE_ENV === 'development') {
    console.debug(`[DEBUG] ${message}`);
    logMessage('DEBUG', message, metadata);
  }
}

module.exports = {
  info,
  warn,
  error,
  debug
};

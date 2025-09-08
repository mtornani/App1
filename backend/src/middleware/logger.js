const fs = require('fs').promises;
const path = require('path');

async function requestLogger(req, res, next) {
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    method: req.method,
    url: req.url,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  };
  
  // Salva nel file di log
  try {
    const logDir = path.join(__dirname, '../../logs');
    await fs.mkdir(logDir, { recursive: true });
    const logFile = path.join(logDir, 'requests.log');
    await fs.appendFile(logFile, JSON.stringify(logEntry) + '\n');
  } catch (error) {
    console.error('Error writing request log:', error);
  }
  
  next();
}

module.exports = requestLogger;

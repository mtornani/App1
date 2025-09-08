const express = require('express');
const cors = require('cors');
require('dotenv').config();

// Middleware
const requestLogger = require('./middleware/logger');
const errorHandler = require('./middleware/errorHandler');

// Routes
const playerRoutes = require('./routes/players');
const runRoutes = require('./routes/run');
const exportRoutes = require('./routes/export');

// Jobs
const { startScheduler } = require('./jobs/scheduler');

// Utils
const { downloadModels } = require('./utils/modelDownloader');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(requestLogger);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Radar SMR Backend is running' });
});

// Routes
app.use('/api/players', playerRoutes);
app.use('/api/run', runRoutes);
app.use('/api/export', exportRoutes);

// Error handling
app.use(errorHandler);

// Download models on startup
downloadModels().then(() => {
  console.log('🚀 Models ready');
  
  // Start server
  const server = app.listen(PORT, () => {
    console.log(`📡 Radar SMR Backend listening on port ${PORT}`);
  });
  
  // Start scheduler
  startScheduler();
  
  // Graceful shutdown
  process.on('SIGTERM', () => {
    console.log('🛑 SIGTERM received, shutting down gracefully');
    server.close(() => {
      console.log('✅ Process terminated');
    });
  });
  
}).catch((error) => {
  console.error('❌ Failed to initialize models:', error);
  process.exit(1);
});

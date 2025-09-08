const express = require('express');
const cors = require('cors');
require('dotenv').config();

const playerRoutes = require('./routes/players');
const runRoutes = require('./routes/run');
const exportRoutes = require('./routes/export');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/players', playerRoutes);
app.use('/api/run', runRoutes);
app.use('/api/export', exportRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Radar SMR Backend is running' });
});

app.listen(PORT, () => {
  console.log(`Radar SMR Backend listening on port ${PORT}`);
});

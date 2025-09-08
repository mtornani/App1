const express = require('express');
const router = express.Router();
const { PrismaClient } = require('@prisma/client');
const csv = require('csv-stringify/sync');

const prisma = new PrismaClient();

// GET /api/export - Esporta dati in CSV o JSON
router.get('/', async (req, res) => {
  try {
    const { format = 'json' } = req.query;
    
    const players = await prisma.player.findMany({
      orderBy: {
        createdAt: 'desc'
      }
    });
    
    if (format === 'csv') {
      // Converti in CSV
      const csvData = csv.stringify(players, {
        header: true,
        columns: [
          'id', 'name', 'dob', 'club', 'role', 'nationality', 
          'track', 'score', 'citizenship_status', 'time_to_eligible_estimate',
          'nat_path_feasibility', 'sources'
        ]
      });
      
      res.header('Content-Type', 'text/csv');
      res.attachment('players.csv');
      res.send(csvData);
    } else {
      // Default a JSON
      res.json(players);
    }
  } catch (error) {
    console.error('Error exporting data:', error);
    res.status(500).json({ error: 'Failed to export data' });
  }
});

module.exports = router;

const express = require('express');
const router = express.Router();
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

// GET /api/players - Ottieni tutti i giocatori
router.get('/', async (req, res) => {
  try {
    const players = await prisma.player.findMany({
      orderBy: {
        createdAt: 'desc'
      }
    });
    res.json(players);
  } catch (error) {
    console.error('Error fetching players:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/players/:id - Ottieni un giocatore specifico
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const player = await prisma.player.findUnique({
      where: { id: parseInt(id) }
    });
    
    if (!player) {
      return res.status(404).json({ error: 'Player not found' });
    }
    
    res.json(player);
  } catch (error) {
    console.error('Error fetching player:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;

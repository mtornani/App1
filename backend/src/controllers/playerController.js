const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function getAllPlayers(req, res) {
  try {
    const players = await prisma.player.findMany({
      orderBy: {
        createdAt: 'desc'
      }
    });
    res.json(players);
  } catch (error) {
    next(error);
  }
}

async function getPlayerById(req, res, next) {
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
    next(error);
  }
}

module.exports = {
  getAllPlayers,
  getPlayerById
};

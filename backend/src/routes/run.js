const express = require('express');
const router = express.Router();

const { runFullRefresh, runLegalAssessment } = require('../services/agent');

// POST /api/run/refresh - Esegui refresh completo (scraping + analisi)
router.post('/refresh', async (req, res) => {
  try {
    console.log('Starting full refresh...');
    await runFullRefresh();
    res.json({ message: 'Full refresh completed successfully' });
  } catch (error) {
    console.error('Error during full refresh:', error);
    res.status(500).json({ error: 'Failed to complete full refresh' });
  }
});

// POST /api/run/legal-assessment - Esegui solo valutazione legale
router.post('/legal-assessment', async (req, res) => {
  try {
    console.log('Starting legal assessment...');
    await runLegalAssessment();
    res.json({ message: 'Legal assessment completed successfully' });
  } catch (error) {
    console.error('Error during legal assessment:', error);
    res.status(500).json({ error: 'Failed to complete legal assessment' });
  }
});

module.exports = router;

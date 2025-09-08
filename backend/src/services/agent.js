const { scrapePlayers } = require('./scraper');
const { processDocuments } = require('./rag');
const { assessLegalEligibility } = require('./legal');
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function runFullRefresh() {
  try {
    console.log('🚀 Starting full refresh...');
    
    // 1. Scraping automatico
    console.log('🔍 Scraping players...');
    const scrapedData = await scrapePlayers();
    
    // 2. Processing RAG
    console.log('🧠 Processing documents with RAG...');
    const extractedPlayers = await processDocuments(scrapedData);
    
    // 3. Salvataggio nel database
    console.log('💾 Saving extracted players...');
    for (const player of extractedPlayers) {
      await savePlayer(player);
    }
    
    // 4. Valutazione legale
    console.log('⚖️ Running legal assessment...');
    await runLegalAssessment();
    
    console.log('✅ Full refresh completed successfully');
  } catch (error) {
    console.error('Error in full refresh:', error);
    throw error;
  }
}

async function runLegalAssessment() {
  try {
    console.log('⚖️ Starting legal assessment...');
    
    // Recupera tutti i giocatori dal database
    const players = await prisma.player.findMany();
    
    console.log(`Processing ${players.length} players...`);
    
    for (const player of players) {
      const legalResult = assessLegalEligibility(player);
      
      // Aggiorna il giocatore con i risultati legali
      await prisma.player.update({
        where: { id: player.id },
        data: {
          track: legalResult.track,
          citizenshipStatus: legalResult.citizenshipStatus,
          natPathFeasibility: legalResult.natPathFeasibility,
          legalNotes: JSON.stringify(legalResult.legalNotes),
          timeToEligibleEstimate: legalResult.timeToEligibleEstimate,
          score: legalResult.score,
          rationale: legalResult.rationale
        }
      });
    }
    
    console.log('✅ Legal assessment completed');
  } catch (error) {
    console.error('Error in legal assessment:', error);
    throw error;
  }
}

async function savePlayer(playerData) {
  try {
    // Verifica se il giocatore esiste già (basato su nome e DOB)
    const existingPlayer = await prisma.player.findFirst({
      where: {
        name: playerData.name,
        dob: playerData.dob
      }
    });
    
    if (existingPlayer) {
      // Aggiorna il giocatore esistente
      return await prisma.player.update({
        where: { id: existingPlayer.id },
        data: {
          ...playerData,
          sources: JSON.stringify(playerData.sources || []),
          residenceHistory: JSON.stringify(playerData.residenceHistory || []),
          updatedAt: new Date()
        }
      });
    } else {
      // Crea nuovo giocatore
      return await prisma.player.create({
        data: {
          ...playerData,
          sources: JSON.stringify(playerData.sources || []),
          residenceHistory: JSON.stringify(playerData.residenceHistory || [])
        }
      });
    }
  } catch (error) {
    console.error('Error saving player:', error);
    throw error;
  }
}

module.exports = {
  runFullRefresh,
  runLegalAssessment
};

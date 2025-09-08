const { getEmbedding } = require('./embedder');
const { extractPlayerInfo } = require('./extractor');

async function processDocuments(documents) {
  try {
    console.log('🧠 Starting RAG processing...');
    
    const extractedPlayers = [];
    
    for (const doc of documents) {
      try {
        // 1. Chunking del documento
        const chunks = chunkText(doc.content, 1000);
        
        // 2. Embedding dei chunk
        const chunkEmbeddings = [];
        for (const chunk of chunks) {
          const embedding = await getEmbedding(chunk);
          chunkEmbeddings.push({
            text: chunk,
            embedding: embedding,
            source: doc.url
          });
        }
        
        // 3. Estrazione informazioni con LLM
        for (const chunkData of chunkEmbeddings) {
          const playerInfo = await extractPlayerInfo(chunkData.text, doc.url);
          if (playerInfo && playerInfo.name) {
            // Aggiungi informazioni di provenienza
            playerInfo.sources = [doc.url];
            playerInfo.extractedFrom = chunkData.text.substring(0, 200) + '...';
            
            // Verifica se il giocatore è già stato estratto
            const existingPlayer = extractedPlayers.find(p => 
              p.name === playerInfo.name && 
              (!p.dob || !playerInfo.dob || p.dob === playerInfo.dob)
            );
            
            if (!existingPlayer) {
              extractedPlayers.push(playerInfo);
            } else {
              // Unisci le informazioni
              mergePlayerInfo(existingPlayer, playerInfo);
            }
          }
        }
      } catch (error) {
        console.error(`Error processing document ${doc.url}:`, error);
      }
    }
    
    console.log(`✅ Extracted ${extractedPlayers.length} unique players`);
    return extractedPlayers;
  } catch (error) {
    console.error('Error in RAG processing:', error);
    throw error;
  }
}

function chunkText(text, chunkSize = 1000) {
  const chunks = [];
  const sentences = text.split(/(?<=[.!?])\s+/);
  
  let currentChunk = '';
  for (const sentence of sentences) {
    if ((currentChunk + sentence).length > chunkSize && currentChunk.length > 0) {
      chunks.push(currentChunk.trim());
      currentChunk = sentence;
    } else {
      currentChunk += ' ' + sentence;
    }
  }
  
  if (currentChunk.length > 0) {
    chunks.push(currentChunk.trim());
  }
  
  return chunks;
}

function mergePlayerInfo(existingPlayer, newPlayerInfo) {
  // Unisci informazioni mancanti
  for (const [key, value] of Object.entries(newPlayerInfo)) {
    if (value && (!existingPlayer[key] || existingPlayer[key] === 'N/D')) {
      existingPlayer[key] = value;
    }
  }
  
  // Unisci fonti
  if (newPlayerInfo.sources) {
    existingPlayer.sources = [...new Set([
      ...(existingPlayer.sources || []),
      ...newPlayerInfo.sources
    ])];
  }
}

module.exports = {
  processDocuments
};

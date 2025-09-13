// backend/src/services/embedder.js
const { pipeline } = require('@xenova/transformers');
let extractor = null;

async function initializeEmbedder() {
  if (!extractor) {
    console.log('🔄 Initializing sentence embedding model...');
    
    // CAMBIA QUESTA RIGA!!!
    // DA: extractor = await pipeline('feature-extraction', 'Xenova/bert-base-uncased');
    // A:
    extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    
    console.log('✅ Sentence embedding model loaded');
  }
  return extractor;
}

async function getEmbedding(text) {
  try {
    if (!text || text.trim().length === 0) {
      return [];
    }
    
    const embedder = await initializeEmbedder();
    const result = await embedder(text, { 
      pooling: 'mean',
      normalize: true  // Aggiungi questo per migliori risultati
    });
    return Array.from(result.data);
  } catch (error) {
    console.error('Error generating embedding:', error);
    return [];
  }
}

module.exports = {
  getEmbedding,
  initializeEmbedder
};

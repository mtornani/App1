// backend-node/src/services/embedder.js
const { pipeline } = require('@xenova/transformers');

let extractor = null;

async function initializeEmbedder() {
  if (!extractor) {
    console.log('🔄 Initializing sentence embedding model...');
    // Usa un modello completamente pubblico e senza autenticazione
    extractor = await pipeline('feature-extraction', 'Xenova/bert-base-uncased');
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
    const result = await embedder(text, { pooling: 'mean' });
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

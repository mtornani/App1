const { pipeline } = require('@xenova/transformers');

let extractor = null;

async function initializeEmbedder() {
  if (!extractor) {
    console.log('🔄 Initializing EmbeddingGemma model...');
    // Usa il nome corretto del modello
    extractor = await pipeline('feature-extraction', 'Xenova/embedding-gemma-300m');
    console.log('✅ EmbeddingGemma model loaded');
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

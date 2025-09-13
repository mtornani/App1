const { pipeline } = require('@xenova/transformers');

let extractor = null;

async function initializeEmbedder() {
  if (!extractor) {
    console.log('🔄 Initializing MiniLM embedder...');
    extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    console.log('✅ MiniLM embedder loaded');
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
      normalize: true 
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

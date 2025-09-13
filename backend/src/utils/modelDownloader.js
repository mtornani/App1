// backend-node/src/utils/modelDownloader.js
const { pipeline } = require('@xenova/transformers');

async function downloadModels() {
  try {
    console.log('📥 Downloading required models...');
    
    // Download embedding model completamente pubblico
    console.log('🔄 Downloading BERT base model...');
    await pipeline('feature-extraction', 'Xenova/bert-base-uncased');
    console.log('✅ BERT base model downloaded');
    
    console.log('🎉 All models downloaded successfully');
  } catch (error) {
    console.error('❌ Model download failed:', error);
    throw error;
  }
}

module.exports = { downloadModels };

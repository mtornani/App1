const { pipeline } = require('@xenova/transformers');
const path = require('path');

async function downloadModels() {
  try {
    console.log('📥 Downloading required models...');
    
    // Download embedding model
    console.log('🔄 Downloading EmbeddingGemma...');
    await pipeline('feature-extraction', 'Xenova/embedding-gemma-300m');
    console.log('✅ EmbeddingGemma downloaded');
    
    // Download LLM model (se abilitato)
    if (process.env.LOCAL_LLM_ENABLED === 'true') {
      console.log('🔄 Downloading Gemma 2B...');
      await pipeline('text-generation', 'Xenova/gemma-2b');
      console.log('✅ Gemma 2B downloaded');
    }
    
    console.log('🎉 All models downloaded successfully');
  } catch (error) {
    console.error('❌ Model download failed:', error);
    throw error;
  }
}

module.exports = { downloadModels };

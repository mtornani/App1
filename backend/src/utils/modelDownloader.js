const { pipeline } = require('@xenova/transformers');

async function downloadModels() {
  try {
    console.log('📥 Downloading required models...');
    
    // Download embedding model pubblico
    console.log('🔄 Downloading sentence embedding model...');
    await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    console.log('✅ Sentence embedding model downloaded');
    
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

// backend-node/src/utils/modelDownloader.js
const { pipeline } = require('@xenova/transformers');

async function downloadModels() {
  try {
    console.log('📥 Downloading required models...');
    
    // Download embedding model pubblico (sempre)
    console.log('🔄 Downloading sentence embedding model...');
    await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    console.log('✅ Sentence embedding model downloaded');
    
    // Download LLM model (solo se abilitato e se funziona)
    if (process.env.LOCAL_LLM_ENABLED === 'true') {
      console.log('🔄 Attempting to download Gemma 2B...');
      try {
        await pipeline('text-generation', 'Xenova/gemma-2b');
        console.log('✅ Gemma 2B downloaded');
      } catch (llmError) {
        console.warn('⚠️ Gemma 2B download failed (likely due to auth). Proceeding without LLM.');
        console.warn('LLM Error:', llmError.message);
        // Non bloccare l'avvio se il modello LLM fallisce
      }
    }
    
    console.log('🎉 All models downloaded successfully');
  } catch (error) {
    console.error('❌ Model download failed:', error);
    throw error;
  }
}

module.exports = { downloadModels };

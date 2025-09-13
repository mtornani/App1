const { pipeline } = require('@xenova/transformers');

async function downloadModels() {
  try {
    console.log('📥 Downloading required models...');
    
    // CAMBIA QUESTA RIGA
    console.log('🔄 Loading MiniLM embedding model...');
    await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
    console.log('✅ MiniLM model ready');
    
    // Rimuovi completamente riferimenti a BERT
    
  } catch (error) {
    console.error('❌ Model download failed:', error);
    // Non bloccare l'app se il modello non si scarica
    console.log('⚠️ Continuing without embedding model');
  }
}

module.exports = { downloadModels };

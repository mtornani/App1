const { pipeline } = require('@xenova/transformers');

async function downloadModels() {
  try {
    console.log('📥 Downloading required models...');
    
    // CAMBIA QUESTA RIGA - USA sentence-transformers INVECE DI Xenova
    console.log('🔄 Downloading sentence embedding model...');
    await pipeline('feature-extraction', 'BAAI/bge-small-en-v1.5');
    console.log('✅ Sentence embedding model downloaded');
    
    // Resto del codice...
    
  } catch (error) {
    console.error('❌ Model download failed:', error);
    console.log('⚠️ Continuing without embedding model');
    // Non bloccare l'app
  }
}

module.exports = { downloadModels };

const { ensureDirectoryExists } = require('../utils/helpers');
const path = require('path');

async function setupModels() {
  try {
    console.log('Setting up models directory...');
    
    // Crea directory per i modelli
    const modelsDir = path.join(__dirname, '../../models');
    await ensureDirectoryExists(modelsDir);
    
    console.log('✅ Models directory ready');
    console.log('Models will be downloaded automatically on first use');
    
  } catch (error) {
    console.error('❌ Models setup failed:', error);
    process.exit(1);
  }
}

// Esegui solo se il file viene eseguito direttamente
if (require.main === module) {
  setupModels();
}

module.exports = { setupModels };

// backend/src/services/embedding-service.js
import { pipeline } from '@xenova/transformers';

class EmbeddingService {
  async initialize() {
    try {
      // USA QUESTO MODELLO - È PUBBLICO E NON RICHIEDE AUTH
      this.embedder = await pipeline(
        'feature-extraction',
        'Xenova/all-MiniLM-L6-v2',  // <-- Cambia qui!
        {
          cache_dir: './models',
          revision: 'main'
        }
      );
      console.log('✅ Model loaded successfully');
    } catch (error) {
      console.error('Error loading model:', error);
      // Fallback a modello ancora più leggero
      this.embedder = await pipeline(
        'feature-extraction',
        'Xenova/all-MiniLM-L12-v2'  // Alternativa
      );
    }
  }
}
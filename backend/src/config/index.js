// Configurazione centralizzata dell'applicazione
require('dotenv').config();

const config = {
  // Server
  server: {
    port: parseInt(process.env.PORT) || 3001,
    host: process.env.HOST || 'localhost'
  },
  
  // Database
  database: {
    url: process.env.DATABASE_URL || 'sqlite://./data/database.sqlite'
  },
  
  // LLM Configuration
  llm: {
    localEnabled: process.env.LOCAL_LLM_ENABLED === 'true',
    openRouterKey: process.env.OPENROUTER_API_KEY,
    gemmaModel: 'Xenova/gemma-2b'
  },
  
  // Embedding
  embedding: {
    model: process.env.EMBEDDING_MODEL || 'Xenova/embedding-gemma-300m'
  },
  
  // Scraping
  scraping: {
    maxPagesPerCrawl: parseInt(process.env.MAX_PAGES_PER_CRAWL) || 50,
    concurrentScrapers: parseInt(process.env.CONCURRENT_SCRAPERS) || 5,
    userAgent: 'RadarSMR/1.0 (Calciatori Eleggibili San Marino)'
  },
  
  // API Keys
  apiKeys: {
    serpapi: process.env.SERPAPI_KEY,
    openrouter: process.env.OPENROUTER_API_KEY
  },
  
  // Legal Rules
  legalRules: {
    fifa: {
      minResidenceYears: 5,
      minResidenceAge: 18
    },
    sanMarino: {
      minResidenceYears: 10,
      allowDualCitizenship: false
    }
  }
};

module.exports = config;

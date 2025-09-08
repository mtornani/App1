const { PrismaClient } = require('@prisma/client');

async function initializeDatabase() {
  const prisma = new PrismaClient();
  
  try {
    console.log('Initializing database...');
    
    // Esegui una query semplice per verificare la connessione
    await prisma.$queryRaw`SELECT 1`;
    
    console.log('✅ Database connection successful');
    console.log('Database initialized successfully');
    
  } catch (error) {
    console.error('❌ Database initialization failed:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

// Esegui solo se il file viene eseguito direttamente
if (require.main === module) {
  initializeDatabase();
}

module.exports = { initializeDatabase };

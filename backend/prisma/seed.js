const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function main() {
  // Esempio di dati di seed (opzionale)
  console.log('Seeding database...');
  
  // Puoi aggiungere qui dati di esempio se necessario
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

# Dockerfile principale per Railway - usa Debian invece di Alpine
FROM node:20-slim

# Installa dipendenze di sistema necessarie
RUN apt-get update && apt-get install -y \
    openssl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia package.json di entrambi i progetti
COPY frontend/package*.json ./frontend/
COPY backend/package*.json ./backend/

# Installa dipendenze
RUN cd frontend && npm install
RUN cd backend && npm install

# Copia schema Prisma e .env
COPY backend/prisma/schema.prisma ./backend/prisma/
COPY backend/.env ./backend/.env

# Crea directory data e genera client Prisma
RUN mkdir -p backend/data
RUN cd backend && npx prisma generate

# Copia tutto il codice
COPY . .

# Build frontend
RUN cd frontend && npm run build

EXPOSE 3000 3001

# Comando di avvio
CMD ["sh", "-c", "cd backend && npm start & cd frontend && npm start"]

# Dockerfile principale per Railway
FROM node:20-alpine

# Installa dipendenze di sistema
RUN apk add --no-cache openssl sqlite

WORKDIR /app

# Copia package.json di entrambi i progetti
COPY frontend/package*.json ./frontend/
COPY backend/package*.json ./backend/

# Installa dipendenze
RUN cd frontend && npm install
RUN cd backend && npm install

# Copia schema Prisma, .env e database
COPY backend/prisma/schema.prisma ./backend/prisma/
COPY backend/.env ./backend/.env
COPY backend/data/ ./backend/data/

# Genera client Prisma
RUN cd backend && npx prisma generate

# Copia tutto il codice
COPY . .

# Build frontend
RUN cd frontend && npm run build

EXPOSE 3000 3001

# Comando di avvio
CMD ["sh", "-c", "cd backend && npm start & cd frontend && npm start"]

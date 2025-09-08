# Dockerfile per Railway - versione semplice
FROM node:18-alpine AS builder

WORKDIR /app

# Copia package.json di entrambi i progetti
COPY frontend/package*.json ./frontend/
COPY backend/package*.json ./backend/

# Installa dipendenze
RUN cd frontend && npm install
RUN cd backend && npm install

# Copia tutto il codice
COPY . .

# Build frontend
RUN cd frontend && npm run build

# Crea directory per dati
RUN mkdir -p backend/data backend/models backend/logs

# Esponi porte
EXPOSE 3000 3001

# Comando di avvio
CMD ["sh", "-c", "cd backend && npm start & cd frontend && npm start"]

# Dockerfile per Railway - versione corretta
FROM node:18-alpine AS builder

WORKDIR /app

# Copia package.json di entrambi i progetti
COPY frontend/package*.json ./frontend/
COPY backend/package*.json ./backend/

# Installa dipendenze frontend
RUN cd frontend && npm install

# Installa dipendenze backend (con legacy peer deps per evitare conflitti)
RUN cd backend && npm install --legacy-peer-deps

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

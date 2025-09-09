FROM node:18-alpine

# Installa le dipendenze di sistema necessarie per Prisma
RUN apk add --no-cache openssl sqlite

WORKDIR /app

# Copia package.json e installa dipendenze
COPY package*.json ./
RUN npm install

# Copia schema Prisma e file di configurazione
COPY prisma/schema.prisma ./prisma/
COPY .env .env

# Genera il client Prisma
RUN npx prisma generate

# Copia tutto il codice
COPY . .

# Crea directory per dati e modelli
RUN mkdir -p data models

EXPOSE 3001

CMD ["npm", "start"]
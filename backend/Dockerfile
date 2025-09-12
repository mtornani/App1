FROM node:20-alpine

# Installa le dipendenze di sistema necessarie
RUN apk add --no-cache openssl sqlite

WORKDIR /app

# Copia package.json e installa dipendenze
COPY package*.json ./
RUN npm install

# Copia schema Prisma, .env e database pre-esistente
COPY prisma/schema.prisma ./prisma/
COPY .env .env
COPY data/ ./data/

# Genera il client Prisma
RUN npx prisma generate

# Copia tutto il codice
COPY . .

# Crea directory per modelli (data esiste già)
RUN mkdir -p models

EXPOSE 3001

CMD ["npm", "start"]

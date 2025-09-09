FROM node:18-alpine

WORKDIR /app

# Copia package.json e installa dipendenze
COPY package*.json ./
RUN npm install

# Copia schema Prisma
COPY prisma/schema.prisma ./prisma/

# Genera il client Prisma
RUN npx prisma generate

# Copia tutto il codice
COPY . .

# Crea directory per dati e modelli
RUN mkdir -p data models

EXPOSE 3001

CMD ["npm", "start"]
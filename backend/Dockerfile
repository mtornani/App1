FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Crea directory per dati e modelli
RUN mkdir -p data models

EXPOSE 3001

CMD ["npm", "start"]

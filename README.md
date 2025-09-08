# Radar SMR - Agente RAG Autonomo per Calciatori

Agente intelligente che cerca, analizza e valuta automaticamente calciatori potenzialmente eleggibili per la nazionale Sanmarinese (FIFA Binario A e B).

## 🚀 Funzionalità

- **Ricerca automatica** di calciatori su Wikipedia, Transfermarkt e altre fonti
- **Pipeline RAG** con embedding locale (`embeddinggemma-300m`)
- **Estrazione dati** con LLM (`gemma-2b` embedded + fallback API)
- **Valutazione legale** secondo regole FIFA e legge Sanmarina
- **Interfaccia web** con shortlist e filtri
- **Export CSV/JSON** dei dati trovati

## 🧰 Stack Tecnologico

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: Node.js + Express
- **Database**: SQLite
- **Embedding**: `google/embeddinggemma-300m` (embedded)
- **LLM**: `gemma-2b` (embedded) + OpenRouter (fallback)
- **Scraping**: Crawlee (Cheerio + Playwright)

## 🐳 Avvio con Docker

\`\`\`bash
# 1. Configura le variabili d'ambiente
cp .env.example .env
# Modifica .env con le tue chiavi API

# 2. Avvia tutto con Docker
docker-compose up

# 3. Accedi all'app
http://localhost:3000
\`\`\`

## 🧪 Avvio Manuale

### Backend
\`\`\`bash
cd backend
npm install
npm start
\`\`\`

### Frontend
\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

## 📤 Export Dati

\`\`\`bash
# Esporta in CSV
curl http://localhost:3001/api/export?format=csv > players.csv

# Esporta in JSON
curl http://localhost:3001/api/export?format=json > players.json
\`\`\`

## 📚 Fonti e Regole

- [Regole Eleggibilità FIFA](https://www.fifa.com/fifa-world-ranking/procedure-and-regulations)
- [Legge Sanmarina sulla Cittadinanza](https://www.sanmarino.it)

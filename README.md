> **Novità: [OpenScout](./openscout/README.md)** — piattaforma di scouting e match
> analysis open-data con *Eligibility Intelligence* per qualsiasi federazione.
> Generalizza Radar SMR e lo trasforma in un'alternativa a costo quasi zero a
> Wyscout/InStat. Strategia di mercato in [openscout/STRATEGY.md](./openscout/STRATEGY.md).

# Radar SMR - Agente RAG Autonomo per Calciatori Eleggibili

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-18.x-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

**Radar SMR** è un agente intelligente RAG (Retrieval-Augmented Generation) che cerca, analizza e valuta automaticamente calciatori potenzialmente eleggibili per la nazionale Sanmarinese secondo le regole della FIFA e le leggi sanmarinesi.

![Radar SMR Architecture](docs/architecture.png)

## 🚀 Funzionalità Principali

- **🔍 Ricerca Autonoma**: Scansione automatica di Wikipedia, Transfermarkt e altre fonti calcistiche
- **🧠 Pipeline RAG Avanzata**: 
  - Web scraping intelligente
  - Chunking semantico
  - Embedding con `google/embeddinggemma-300m` (embedded)
  - Estrazione dati con `gemma-2b` (embedded + fallback API)
- **⚖️ Valutazione Legale Automatica**:
  - Binario A: Giocatori immediatamente convocabili (NOW)
  - Binario B: Oriundi naturalizzabili (WHAT_IF)
  - Score di eleggibilità e tempistiche
- **🖥️ Interfaccia Web Intuitiva**:
  - Shortlist con filtri avanzati
  - Dettaglio giocatore con fonti e citazioni
  - Export CSV/JSON dei dati
- **📦 Zero Costi API**: Modelli embedded per embedding ed estrazione

## 🧰 Stack Tecnologico

### Frontend
- **Next.js 14** + TypeScript
- **Tailwind CSS** + shadcn/ui
- **React** Components

### Backend
- **Node.js** + Express
- **SQLite** Database (Prisma ORM)
- **Crawlee** per web scraping
- **@xenova/transformers** per modelli embedded:
  - `google/embeddinggemma-300m` per embedding
  - `gemma-2b` per estrazione dati
- **Regole legali** integrate (FIFA + San Marino)

### Infrastruttura
- **Docker Compose** per deploy
- **Multi-container** architecture

## 🏗️ Avvio Rapido

### Prerequisiti
- Docker e Docker Compose
- Node.js 18+ (per sviluppo locale)

### Setup Iniziale

1. **Clona il repository**:
   ```bash
   git clone https://github.com/tuo-username/radar-smr.git
   cd radar-smr
   2. **Configura le variabili d'ambiente**:
   ```bash
   cp .env.example .env
   # Modifica .env con le tue chiavi API (opzionali per fallback)
   ```

3. **Avvia con Docker**:
   ```bash
   docker-compose up -d
   ```

4. **Accedi all'applicazione**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:3001

### Comandi Utili

```bash
# Avvia ricerca automatica
curl -X POST http://localhost:3001/api/run/refresh

# Esegui solo valutazione legale
curl -X POST http://localhost:3001/api/run/legal-assessment

# Esporta dati in CSV
curl http://localhost:3001/api/export?format=csv > players.csv

# Esporta dati in JSON
curl http://localhost:3001/api/export?format=json > players.json
```

## 📊 Struttura del Progetto

```
radar-smr/
├── frontend/           # Interfaccia Next.js
├── backend/            # API Node.js + RAG pipeline
├── docker-compose.yml  # Configurazione Docker
├── .env.example        # Template configurazione
└── README.md           # Questo file
```

## 🔧 Configurazione

### Variabili d'Ambiente (.env)

```env
# API Keys (opzionali per fallback)
OPENROUTER_API_KEY=tua_chiave_openrouter
SERPAPI_KEY=tua_chiave_serpapi

# Modalità LLM
LOCAL_LLM_ENABLED=true

# Database
DATABASE_URL=sqlite://./data/database.sqlite
```

## 🧪 Testing

```bash
# Test backend
cd backend
npm test

# Test frontend
cd frontend
npm test
```

## 📤 Export Dati

L'applicazione supporta export in:
- **CSV**: compatto e leggibile
- **JSON**: completo con tutti i campi

Accessibili via UI o API.

## 📚 Fonti e Regole Legal

### Regole FIFA
- Nascita in San Marino
- Ascendenza diretta (genitore/nonno)
- 5 anni di residenza post-18

### Legge Sanmarinese
- 10 anni di residenza continua
- Rinuncia alla cittadinanza precedente
- Valutazione caso per caso

## 🤝 Contribuire

1. Fork del repository
2. Crea branch feature (`git checkout -b feature/NuovaFeature`)
3. Commit changes (`git commit -am 'Aggiungi nuova feature'`)
4. Push al branch (`git push origin feature/NuovaFeature`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT - vedi il file [LICENSE](LICENSE) per dettagli.

## 🙏 Crediti

- **Google** per il modello `embeddinggemma-300m`
- **Hugging Face** per l'ecosistema transformers
- **Xenova** per `transformers.js`
- Tutti i contributor del progetto open source

## 📞 Supporto

Per problemi o domande:
- Apri una issue su GitHub
- Contatta il maintainer
```

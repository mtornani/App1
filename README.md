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

const fs = require('fs').promises;
const path = require('path');

// Funzione per creare directory se non esistono
async function ensureDirectoryExists(dirPath) {
  try {
    await fs.access(dirPath);
  } catch (error) {
    if (error.code === 'ENOENT') {
      await fs.mkdir(dirPath, { recursive: true });
    } else {
      throw error;
    }
  }
}

// Funzione per normalizzare il testo (rimuove spazi extra, ecc.)
function normalizeText(text) {
  if (!text) return '';
  return text.replace(/\s+/g, ' ').trim();
}

// Funzione per calcolare l'età da una data di nascita
function calculateAge(dob) {
  if (!dob) return null;
  const birthDate = new Date(dob);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  
  return age;
}

// Funzione per validare una data nel formato YYYY-MM-DD
function isValidDate(dateString) {
  if (!dateString) return false;
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(dateString)) return false;
  
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date);
}

// Funzione per formattare le fonti
function formatSources(sources) {
  if (!sources) return [];
  if (typeof sources === 'string') {
    try {
      return JSON.parse(sources);
    } catch (error) {
      return [sources];
    }
  }
  return Array.isArray(sources) ? sources : [sources];
}

module.exports = {
  ensureDirectoryExists,
  normalizeText,
  calculateAge,
  isValidDate,
  formatSources
};

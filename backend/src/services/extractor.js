const { runLLM } = require('./llm');

async function extractPlayerInfo(textChunk, sourceUrl) {
  try {
    const prompt = `
Analizza il seguente testo e estrai le informazioni di un calciatore se presenti.
Restituisci SOLO un JSON valido con i seguenti campi:

{
  "name": "nome completo del giocatore",
  "dob": "data di nascita in formato YYYY-MM-DD (se disponibile)",
  "club": "club attuale (se disponibile)",
  "role": "ruolo (es. Portiere, Difensore, Centrocampista, Attaccante)",
  "nationality": "nazionalità (codice ISO, es. ITA, SMR, ARG)",
  "residenceHistory": [
    {
      "country": "codice paese",
      "years": "anni di residenza (numero)"
    }
  ]
}

Testo da analizzare:
"${textChunk}"

Importante:
- Se non trovi informazioni specifiche, lascia il campo vuoto o null
- NON aggiungere testo esplicativo, SOLO il JSON
- Se non è un calciatore, restituisci null
`;

    const response = await runLLM(prompt);
    
    if (!response) {
      return null;
    }
    
    // Pulizia della risposta
    let jsonString = response.trim();
    
    // Rimuovi eventuali markdown o testo extra
    if (jsonString.startsWith('```json')) {
      jsonString = jsonString.substring(7);
    }
    if (jsonString.startsWith('```')) {
      jsonString = jsonString.substring(3);
    }
    if (jsonString.endsWith('```')) {
      jsonString = jsonString.substring(0, jsonString.length - 3);
    }
    
    try {
      const playerData = JSON.parse(jsonString);
      
      // Validazione base
      if (playerData.name && playerData.name.trim() !== '') {
        return {
          ...playerData,
          name: playerData.name.trim(),
          dob: playerData.dob || null,
          club: playerData.club || null,
          role: playerData.role || null,
          nationality: playerData.nationality || null
        };
      }
    } catch (parseError) {
      console.error('Error parsing LLM response:', parseError);
      console.error('Raw response:', response);
    }
    
    return null;
  } catch (error) {
    console.error('Error extracting player info:', error);
    return null;
  }
}

module.exports = {
  extractPlayerInfo
};

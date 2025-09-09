// Regole FIFA per l'eleggibilità
const FIFA_RULES = {
  MIN_RESIDENCE_YEARS: 5,
  MIN_RESIDENCE_AGE: 18
};

// Regole Sanmarinesi per la cittadinanza
const SMR_CITIZENSHIP_RULES = {
  MIN_RESIDENCE_YEARS: 10,
  ALLOW_DUAL_CITIZENSHIP: false // La legge sanmarinese generalmente non permette doppia cittadinanza
};

function assessLegalEligibility(player) {
  const result = {
    track: null,
    citizenshipStatus: 'unknown',
    natPathFeasibility: '',
    legalNotes: [],
    timeToEligibleEstimate: null,
    score: 0,
    rationale: ''
  };
  
  try {
    // 1. Determina lo stato della cittadinanza
    const citizenshipInfo = determineCitizenshipStatus(player);
    result.citizenshipStatus = citizenshipInfo.status;
    result.legalNotes.push(...citizenshipInfo.notes);
    
    // 2. Valuta l'eleggibilità immediata (Binario A - NOW)
    const immediateEligibility = checkImmediateEligibility(player, citizenshipInfo);
    if (immediateEligibility.eligible) {
      result.track = 'NOW';
      result.score = 100;
      result.rationale = immediateEligibility.reason;
      result.legalNotes.push('Giocatore immediatamente convocabile secondo regole FIFA');
      return result;
    }
    
    // 3. Valuta la potenziale eleggibilità futura (Binario B - WHAT_IF)
    const potentialEligibility = checkPotentialEligibility(player, citizenshipInfo);
    result.track = 'WHAT_IF';
    result.score = potentialEligibility.score;
    result.rationale = potentialEligibility.reason;
    result.natPathFeasibility = potentialEligibility.feasibility;
    result.timeToEligibleEstimate = potentialEligibility.timeEstimate;
    
    if (potentialEligibility.feasible) {
      result.legalNotes.push('Percorso di naturalizzazione potenzialmente fattibile');
    } else {
      result.legalNotes.push('Percorso di naturalizzazione non fattibile o molto complesso');
    }
    
  } catch (error) {
    console.error('Error in legal assessment for player:', player.name, error);
    result.legalNotes.push('Errore durante la valutazione legale: ' + error.message);
  }
  
  return result;
}

function determineCitizenshipStatus(player) {
  const result = {
    status: 'unknown',
    notes: []
  };
  
  // Controllo diretto della cittadinanza SMR
  if (player.nationality === 'SMR') {
    result.status = 'has_SMR';
    result.notes.push('Giocatore dichiara già cittadinanza sanmarinese');
    return result;
  }
  
  // Analisi della storia di residenza
  let smrResidenceYears = 0;
  let totalResidenceYears = 0;
  
  if (player.residenceHistory) {
    try {
      const residenceHistory = typeof player.residenceHistory === 'string' 
        ? JSON.parse(player.residenceHistory) 
        : player.residenceHistory;
      
      for (const entry of residenceHistory) {
        totalResidenceYears += entry.years || 0;
        if (entry.country === 'SMR') {
          smrResidenceYears += entry.years || 0;
        }
      }
    } catch (error) {
      console.warn('Error parsing residence history:', error);
    }
  }
  
  // Determina lo stato della cittadinanza
  if (smrResidenceYears >= SMR_CITIZENSHIP_RULES.MIN_RESIDENCE_YEARS) {
    result.status = 'has_SMR';
    result.notes.push(`Giocatore ha risieduto in San Marino per ${smrResidenceYears} anni (soglia: ${SMR_CITIZENSHIP_RULES.MIN_RESIDENCE_YEARS})`);
  } else if (smrResidenceYears > 0) {
    result.status = 'no_SMR';
    result.notes.push(`Giocatore ha risieduto in San Marino per ${smrResidenceYears} anni (inferiore alla soglia di ${SMR_CITIZENSHIP_RULES.MIN_RESIDENCE_YEARS} anni richiesta)`);
  } else {
    result.status = 'no_SMR';
    result.notes.push('Nessuna residenza documentata in San Marino');
  }
  
  return result;
}

function checkImmediateEligibility(player, citizenshipInfo) {
  // Controllo hard-stop: cap senior con altra nazionale ufficiale
  if (player.hasPlayedSeniorNationalTeam && player.nationality !== 'SMR') {
    return {
      eligible: false,
      reason: 'Giocatore ha già rappresentato nazionale senior ufficiale con altra nazionalità'
    };
  }
  
  // Controllo cittadinanza SMR
  if (citizenshipInfo.status !== 'has_SMR') {
    return {
      eligible: false,
      reason: 'Giocatore non possiede cittadinanza sanmarinese'
    };
  }
  
  // Controllo requisiti FIFA
  const fifaEligible = checkFifaRequirements(player);
  if (!fifaEligible.eligible) {
    return fifaEligible;
  }
  
  return {
    eligible: true,
    reason: 'Giocatore soddisfa tutti i requisiti per la cittadinanza SMR e le regole FIFA'
  };
}

function checkFifaRequirements(player) {
  // Controllo nascita in San Marino
  if (player.birthCountry === 'SMR') {
    return {
      eligible: true,
      reason: 'Giocatore nato in San Marino'
    };
  }
  
  // Controllo ascendenti (genitore/nonno sanmarinese)
  if (player.hasSanMarinoAncestors) {
    return {
      eligible: true,
      reason: 'Giocatore con ascendenti sanmarinesi diretti'
    };
  }
  
  // Controllo residenza post-18
  let post18ResidenceYears = 0;
  if (player.residenceHistory) {
    try {
      const residenceHistory = typeof player.residenceHistory === 'string' 
        ? JSON.parse(player.residenceHistory) 
        : player.residenceHistory;
      
      // Calcola anni di residenza dopo i 18 anni
      const currentAge = player.dob ? Math.floor((new Date() - new Date(player.dob)) / (365.25 * 24 * 60 * 60 * 1000)) : 0;
      const ageAtStartOfResidence = currentAge; // Semplificazione
      
      for (const entry of residenceHistory) {
        if (entry.country === 'SMR' && ageAtStartOfResidence >= 18) {
          post18ResidenceYears += entry.years || 0;
        }
      }
    } catch (error) {
      console.warn('Error parsing residence history for FIFA check:', error);
    }
  }
  
  if (post18ResidenceYears >= FIFA_RULES.MIN_RESIDENCE_YEARS) {
    return {
      eligible: true,
      reason: `Giocatore ha risieduto in San Marino per ${post18ResidenceYears} anni dopo i 18 anni (soglia FIFA: ${FIFA_RULES.MIN_RESIDENCE_YEARS})`
    };
  }
  
  return {
    eligible: false,
    reason: `Giocatore non soddisfa i requisiti FIFA per la rappresentazione (residenza post-18: ${post18ResidenceYears} anni, richiesti: ${FIFA_RULES.MIN_RESIDENCE_YEARS})`
  };
}

function checkPotentialEligibility(player, citizenshipInfo) {
  const result = {
    feasible: false,
    score: 0,
    reason: '',
    feasibility: '',
    timeEstimate: null
  };
  
  // Se già cittadino SMR, non è un caso "WHAT_IF"
  if (citizenshipInfo.status === 'has_SMR') {
    result.feasible = true;
    result.score = 90;
    result.reason = 'Giocatore già cittadino sanmarinese';
    result.feasibility = 'Già cittadino';
    result.timeEstimate = 0;
    return result;
  }
  
  // Analisi fattibilità naturalizzazione
  const naturalizationFeasibility = analyzeNaturalizationFeasibility(player);
  result.feasible = naturalizationFeasibility.feasible;
  result.feasibility = naturalizationFeasibility.explanation;
  result.timeEstimate = naturalizationFeasibility.timeEstimate;
  
  // Calcolo score basato su vari fattori
  let score = 0;
  const factors = [];
  
  // Prossimità territoriale (Italia = +30 punti)
  if (player.nationality === 'ITA') {
    score += 30;
    factors.push('Prossimità territoriale con San Marino');
  }
  
  // Residenza in San Marino (se presente)
  let smrResidenceYears = 0;
  if (player.residenceHistory) {
    try {
      const residenceHistory = typeof player.residenceHistory === 'string' 
        ? JSON.parse(player.residenceHistory) 
        : player.residenceHistory;
      
      for (const entry of residenceHistory) {
        if (entry.country === 'SMR') {
          smrResidenceYears += entry.years || 0;
        }
      }
    } catch (error) {
      console.warn('Error parsing residence history:', error);
    }
  }
  
  if (smrResidenceYears > 0) {
    const residenceScore = Math.min(40, smrResidenceYears * 8); // Max 40 punti
    score += residenceScore;
    factors.push(`Residenza in San Marino: ${smrResidenceYears} anni`);
  }
  
  // Età (giovane = più tempo per naturalizzazione = + punti)
  if (player.dob) {
    const age = Math.floor((new Date() - new Date(player.dob)) / (365.25 * 24 * 60 * 60 * 1000));
    if (age < 25) {
      score += 15;
      factors.push('Età giovane, tempo sufficiente per naturalizzazione');
    } else if (age < 30) {
      score += 10;
      factors.push('Età media, tempo moderato per naturalizzazione');
    }
  }
  
  // Fattibilità naturalizzazione
  if (naturalizationFeasibility.feasible) {
    score += 25;
  }
  
  result.score = Math.min(100, Math.max(0, score));
  result.reason = factors.join('; ') || 'Nessun fattore positivo identificato';
  
  return result;
}

function analyzeNaturalizationFeasibility(player) {
  const result = {
    feasible: false,
    explanation: '',
    timeEstimate: null
  };
  
  // Controllo residenza attuale
  let smrResidenceYears = 0;
  if (player.residenceHistory) {
    try {
      const residenceHistory = typeof player.residenceHistory === 'string' 
        ? JSON.parse(player.residenceHistory) 
        : player.residenceHistory;
      
      for (const entry of residenceHistory) {
        if (entry.country === 'SMR') {
          smrResidenceYears += entry.years || 0;
        }
      }
    } catch (error) {
      console.warn('Error parsing residence history:', error);
    }
  }
  
  const yearsNeeded = Math.max(0, SMR_CITIZENSHIP_RULES.MIN_RESIDENCE_YEARS - smrResidenceYears);
  result.timeEstimate

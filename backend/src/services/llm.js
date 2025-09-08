const { pipeline } = require('@xenova/transformers');

// Configurazione modalità LLM
const LOCAL_LLM_ENABLED = process.env.LOCAL_LLM_ENABLED === 'true';
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;

let localLLM = null;

async function initializeLocalLLM() {
  if (!LOCAL_LLM_ENABLED) return null;
  
  if (!localLLM) {
    console.log('🔄 Initializing Gemma 2B model...');
    try {
      localLLM = await pipeline('text-generation', 'Xenova/gemma-2b');
      console.log('✅ Gemma 2B model loaded');
    } catch (error) {
      console.error('Failed to load Gemma 2B model:', error);
      localLLM = null;
    }
  }
  return localLLM;
}

async function runLocalLLM(prompt) {
  try {
    const llm = await initializeLocalLLM();
    if (!llm) {
      throw new Error('Local LLM not initialized');
    }
    
    const result = await llm(prompt, {
      max_new_tokens: 500,
      temperature: 0.7,
      do_sample: true
    });
    
    return result[0].generated_text;
  } catch (error) {
    console.error('Error running local LLM:', error);
    throw error;
  }
}

async function runOpenRouterLLM(prompt) {
  if (!OPENROUTER_API_KEY) {
    throw new Error('OPENROUTER_API_KEY not configured');
  }
  
  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'google/gemma-2b-it',
        messages: [
          { role: 'user', content: prompt }
        ],
        temperature: 0.7,
        max_tokens: 500
      })
    });
    
    const data = await response.json();
    
    if (data.choices && data.choices[0] && data.choices[0].message) {
      return data.choices[0].message.content;
    }
    
    throw new Error('Invalid response from OpenRouter');
  } catch (error) {
    console.error('Error calling OpenRouter:', error);
    throw error;
  }
}

async function runLLM(prompt) {
  // Prova prima con LLM locale
  if (LOCAL_LLM_ENABLED) {
    try {
      return await runLocalLLM(prompt);
    } catch (localError) {
      console.warn('Local LLM failed, falling back to API:', localError.message);
    }
  }
  
  // Fallback su API
  if (OPENROUTER_API_KEY) {
    try {
      return await runOpenRouterLLM(prompt);
    } catch (apiError) {
      console.error('API LLM failed:', apiError.message);
      throw new Error('Both local and API LLM failed');
    }
  }
  
  throw new Error('No LLM available (configure LOCAL_LLM_ENABLED or OPENROUTER_API_KEY)');
}

module.exports = {
  runLLM
};

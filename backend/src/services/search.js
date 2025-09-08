const fetch = require('node-fetch');

// Wikipedia Search
async function wikipediaSearch(query) {
  try {
    const encodedQuery = encodeURIComponent(query);
    const url = `https://it.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodedQuery}&format=json&srlimit=10`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    return data.query.search.map(result => ({
      url: `https://it.wikipedia.org/wiki/${result.title.replace(/ /g, '_')}`,
      title: result.title,
      snippet: result.snippet
    }));
  } catch (error) {
    console.error('Error in Wikipedia search:', error);
    return [];
  }
}

// Google Search (con SerpAPI)
async function googleSearch(query) {
  if (!process.env.SERPAPI_KEY) {
    console.log('⚠️  SERPAPI_KEY not configured, skipping Google search');
    return [];
  }
  
  try {
    const encodedQuery = encodeURIComponent(query);
    const url = `https://serpapi.com/search.json?engine=google&q=${encodedQuery}&api_key=${process.env.SERPAPI_KEY}&gl=it&hl=it`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    if (data.organic_results) {
      return data.organic_results.map(result => ({
        url: result.link,
        title: result.title,
        snippet: result.snippet
      }));
    }
    
    return [];
  } catch (error) {
    console.error('Error in Google search:', error);
    return [];
  }
}

module.exports = {
  wikipediaSearch,
  googleSearch
};

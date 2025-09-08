const { Dataset, CheerioCrawler } = require('crawlee');
const { wikipediaSearch, googleSearch } = require('./search');

const SEARCH_QUERIES = [
  "calciatori italiani con residenza in San Marino",
  "giocatori calcio San Marino nazionalità",
  "cittadini stranieri calcio San Marino",
  "calciatori oriundi San Marino FIFA",
  "residenza San Marino calcio naturalizzazione"
];

async function scrapePlayers() {
  try {
    console.log('🔍 Starting player scraping...');
    
    const allResults = [];
    
    // 1. Ricerca su Wikipedia
    console.log('📖 Searching Wikipedia...');
    for (const query of SEARCH_QUERIES) {
      const wikiResults = await wikipediaSearch(query);
      allResults.push(...wikiResults);
    }
    
    // 2. Ricerca su Google (se API key disponibile)
    if (process.env.SERPAPI_KEY) {
      console.log('🔍 Searching Google...');
      for (const query of SEARCH_QUERIES) {
        const googleResults = await googleSearch(query);
        allResults.push(...googleResults);
      }
    }
    
    // 3. Scraping delle pagine trovate
    console.log(`📄 Scraping ${allResults.length} pages...`);
    const scrapedContent = await scrapeWebPages(allResults);
    
    console.log(`✅ Scraped ${scrapedContent.length} documents`);
    return scrapedContent;
  } catch (error) {
    console.error('Error in player scraping:', error);
    throw error;
  }
}

async function scrapeWebPages(urls) {
  const scrapedData = [];
  
  const crawler = new CheerioCrawler({
    maxRequestsPerCrawl: parseInt(process.env.MAX_PAGES_PER_CRAWL) || 50,
    requestHandler: async ({ $, request }) => {
      try {
        const title = $('title').text().trim();
        const content = $('body').text().trim();
        
        if (content.length > 100) { // Solo contenuti significativi
          scrapedData.push({
            url: request.url,
            title,
            content,
            scrapedAt: new Date()
          });
        }
      } catch (error) {
        console.error(`Error scraping ${request.url}:`, error);
      }
    },
  });
  
  const requests = urls.map(url => ({ url }));
  await crawler.run(requests);
  
  return scrapedData;
}

module.exports = {
  scrapePlayers
};

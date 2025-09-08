export default function AboutPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Informazioni su Radar SMR</h1>
        
        <div className="space-y-6">
          <section>
            <h2 className="text-xl font-semibold mb-3">Cos'è Radar SMR?</h2>
            <p className="text-muted-foreground">
              Radar SMR è un agente intelligente che cerca, analizza e valuta automaticamente 
              calciatori potenzialmente eleggibili per la nazionale Sanmarinese secondo le regole 
              della FIFA e le leggi sanmarinesi.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">Come Funziona</h2>
            <ul className="list-disc list-inside space-y-2 text-muted-foreground">
              <li>Ricerca automatica su Wikipedia, Transfermarkt e altre fonti calcistiche</li>
              <li>Analisi dei dati con modelli linguistici avanzati (embedding e LLM)</li>
              <li>Valutazione legale secondo criteri FIFA e normativa sanmarinese</li>
              <li>Classificazione in "NOW" (eleggibili ora) e "WHAT_IF" (potenzialmente eleggibili)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">Binari di Eleggibilità</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium">Binario A - NOW (Convocabili Ora)</h3>
                <p className="text-sm text-muted-foreground">
                  Giocatori che possiedono già la cittadinanza sanmarinese e soddisfano i requisiti FIFA: 
                  nascita in SMR, ascendenza diretta, o 5 anni di residenza post-18.
                </p>
              </div>
              <div>
                <h3 className="font-medium">Binario B - WHAT_IF (Oriundi Naturalizzabili)</h3>
                <p className="text-sm text-muted-foreground">
                  Giocatori non ancora eleggibili ma che potrebbero diventarlo attraverso la 
                  naturalizzazione sanmarinese, valutando prossimità territoriale, legami familiari 
                  e fattibilità legale.
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">Tecnologie Utilizzate</h2>
            <ul className="list-disc list-inside space-y-2 text-muted-foreground">
              <li>Next.js 14 + TypeScript + Tailwind CSS</li>
              <li>Modelli embeddinggemma-300m per analisi semantica</li>
              <li>Gemma 2B per estrazione dati avanzata</li>
              <li>SQLite per database locale</li>
              <li>Docker per deploy semplificato</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  )
}

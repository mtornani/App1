---
type: source
title: Call K-Sport del 23 settembre — solo Bobo, Marcolini assente
updated: 2026-09-23
sources: [raw/k-sport-call-2026-09-23.md]
status: attiva
---

# Call K-Sport, 23 settembre, ore 14:40

Presente solo Roberto Federiconi ("Bobo", `bobo@k-sport.tech`). Marcolini
assente, riceverà un resoconto da Bobo.

## Cosa dice la fonte

Bobo ha i link delle repo [[entita-sentinel]], [[entita-ob1]] (variante
Global e variante Lega Pro). Il suo obiettivo è capire come integrare gli
output di questi sistemi in **Dynamix 2**, il sistema di punta di K-Sport.
Non è chiaro se K-Sport vuole integrare tutti e tre i sistemi o solo OB1
Global — Mirko ha scelto di non forzare la risposta e aspettare che siano
loro a chiarirlo.

Marcolini (via Bobo) ha proposto di dividersi i guadagni. La fonte lo
qualifica esplicitamente come segnale commerciale, non un accordo chiuso:
nessuna percentuale è stata discussa né tanto meno chiusa.

## Accordo operativo stabilito con K-Sport

Aspettare che Marcolini si faccia vivo. Non inseguire Bobo via mail.

## Decisioni di linea prodotto, interne

* Lega Pro e Global di [[entita-ob1]] sono valutati identici → da valutare
  la fusione in un solo output verso Dynamix. **Non ancora decisa**, è una
  valutazione aperta.
* [[entita-sentinel]] resta separato: niente fusione di codice con OB1.
  Gancio tecnico possibile via Postgres + Cloud Run.

## Frame che Mirko vuole tenere

K-Sport è trattato come fornitore/integrazione upstream ("diga"), non come
un pitch verso un ATS. Lo split dei guadagni si discute solo dopo che il
perimetro tecnico (quanti sistemi, quale integrazione) è chiaro.

## Vincoli dichiarati per chi lavora su questo dopo

* Non aprire nuovi thread commerciali con K-Sport di iniziativa.
* Non attribuire a K-Sport fatti non confermati dalla fonte (es. titolo
  CTO o bio Namirial di una controparte) — [DATO MANCANTE: a chi si
  riferisse la nota "titolo CTO / bio Namirial", la fonte non lo esplicita,
  solo il divieto di inventarlo].
* Grok esegue sui progetti interni ripresi da questa call; questa sessione
  (Jarvis) tiene il pensiero/agency, non l'esecuzione del thread K-Sport.

## Stato a fine fonte

In attesa che Marcolini si faccia vivo. Vedi [[thread-k-sport-dynamix]].

"""Agenzia autonoma: team di agenti che gira senza server presidiato.

Tre modi di esecuzione, stesso codice:
  - locale:  python -m agency run <mission_id>
  - cloud:   GitHub Actions (cron + dispatch) esegue le missioni pending
  - mobile:  la PWA in agency/web crea missioni e legge i risultati
"""

__version__ = "0.1.0"

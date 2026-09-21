"""Il brief: il sistema parla per primo, senza chiamare nessun modello.

Perche' deterministico e non generato. Tre motivi concreti:
  - costa zero, quindi lo puoi lanciare venti volte al giorno;
  - e' istantaneo e funziona offline;
  - non puo' allucinare. Dice solo quello che sta scritto nel vault.

Un assistente che ti dice ogni mattina una cosa sbagliata con tono sicuro e'
peggio di nessun assistente. Qui i fatti vengono dal frontmatter, punto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from . import config

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Oltre questi giorni un filo aperto e' fermo, non in lavorazione.
GIORNI_FERMO = 21
GIORNI_ABBANDONO = 90


@dataclass
class Pagina:
    """Una pagina del vault, letta dal frontmatter."""

    slug: str
    tipo: str = ""
    titolo: str = ""
    aggiornata: Optional[date] = None
    stato: str = ""
    # Dipendenza DICHIARATA: "questo filo aspetta questi altri".
    # Dedurla dai wikilink non funziona: "A blocca B" e "A dipende da B" si
    # scrivono con lo stesso link, e indovinare significa sbagliare meta' volte.
    bloccato_da: List[str] = field(default_factory=list)
    blocca: List[str] = field(default_factory=list)

    @property
    def giorni(self) -> Optional[int]:
        return (date.today() - self.aggiornata).days if self.aggiornata else None

    @property
    def aperta(self) -> bool:
        return self.tipo == "thread" and self.stato not in ("chiuso", "abbandonato")


def _parse_frontmatter(testo: str) -> Dict[str, str]:
    """Legge il frontmatter senza dipendere da un parser YAML.

    I campi usati dal brief sono scalari su una riga, piu' le liste in stile
    inline `[a, b]`. Basta questo: aggiungere una dipendenza per un parser
    completo, per cinque campi, non si giustifica.
    """

    match = FRONTMATTER_RE.match(testo)
    if not match:
        return {}
    campi: Dict[str, str] = {}
    for riga in match.group(1).splitlines():
        if riga.startswith((" ", "\t", "-")) or ":" not in riga:
            continue
        chiave, _, valore = riga.partition(":")
        campi[chiave.strip()] = valore.strip().strip("\"'")
    return campi


def _parse_lista(valore: str) -> List[str]:
    """Legge una lista inline `[uno, due]`, tollerando i wikilink dentro."""

    grezzo = valore.strip()
    if grezzo.startswith("[") and grezzo.endswith("]"):
        grezzo = grezzo[1:-1]
    voci = []
    for pezzo in grezzo.split(","):
        pulito = pezzo.strip().strip("\"'").strip()
        pulito = pulito.removeprefix("[[").removesuffix("]]")
        if pulito:
            voci.append(pulito)
    return voci


def _parse_data(valore: str) -> Optional[date]:
    try:
        return datetime.strptime(valore, "%Y-%m-%d").date()
    except ValueError:
        return None


def leggi_vault(vault_dir: Optional[Path] = None) -> Dict[str, Pagina]:
    """Carica le pagine e calcola i link entranti.

    I link entranti sono il segnale che conta: una pagina citata da altre e'
    un blocco, non un dettaglio.
    """

    base = (vault_dir or config.VAULT_DIR) / "wiki"
    pagine: Dict[str, Pagina] = {}
    if not base.is_dir():
        return pagine

    for percorso in sorted(base.glob("*.md")):
        testo = percorso.read_text(encoding="utf-8", errors="replace")
        campi = _parse_frontmatter(testo)
        pagina = Pagina(
            slug=percorso.stem,
            tipo=campi.get("type", ""),
            titolo=campi.get("title", percorso.stem),
            aggiornata=_parse_data(campi.get("updated", "")),
            stato=campi.get("status", ""),
            bloccato_da=_parse_lista(campi.get("blocked_by", "")),
        )
        pagine[pagina.slug] = pagina

    # Lato inverso: chi aspetta me. E' il segnale che decide le priorita'.
    for pagina in pagine.values():
        for bloccante in pagina.bloccato_da:
            if bloccante in pagine and bloccante != pagina.slug:
                pagine[bloccante].blocca.append(pagina.slug)

    return pagine


def _punteggio(pagina: Pagina, pagine: Dict[str, Pagina]) -> int:
    """Quanto pesa un filo aperto. Piu' alto, piu' va affrontato prima.

    Il criterio dominante non e' l'anzianita' ma quanti altri fili aspettano
    questo: sbloccare una cosa che ne sblocca tre vale piu' che chiudere
    la piu' vecchia.
    """

    bloccati = sum(1 for slug in pagina.blocca if pagine[slug].aperta)
    punteggio = bloccati * 100
    # Un filo che aspetta qualcos'altro non puo' essere "la cosa da fare adesso".
    if any(pagine[s].aperta for s in pagina.bloccato_da if s in pagine):
        punteggio -= 1000
    giorni = pagina.giorni
    if giorni is not None:
        punteggio += min(giorni, GIORNI_ABBANDONO)
        if giorni >= GIORNI_FERMO:
            punteggio += 50
    return punteggio


def componi(vault_dir: Optional[Path] = None) -> Dict[str, object]:
    """Il brief come dati. La formattazione sta altrove."""

    pagine = leggi_vault(vault_dir)
    aperti = [p for p in pagine.values() if p.aperta]
    aperti.sort(key=lambda p: _punteggio(p, pagine), reverse=True)

    def bloccati_da(pagina: Pagina) -> List[str]:
        """I fili che aspettano questo."""

        return [pagine[slug].titolo for slug in pagina.blocca if pagine[slug].aperta]

    fermi = [p for p in aperti if (p.giorni or 0) >= GIORNI_FERMO]
    da_rivedere = [
        p for p in pagine.values()
        if p.tipo == "decision" and p.stato not in ("attiva", "")
    ]

    return {
        "vault": str((vault_dir or config.VAULT_DIR)),
        "pagine_totali": len(pagine),
        "prima_cosa": (
            {
                "titolo": aperti[0].titolo,
                "slug": aperti[0].slug,
                "giorni": aperti[0].giorni,
                "blocca": bloccati_da(aperti[0]),
            }
            if aperti else None
        ),
        "altri_aperti": [
            {"titolo": p.titolo, "slug": p.slug, "giorni": p.giorni,
             "blocca": bloccati_da(p)}
            for p in aperti[1:]
        ],
        "fermi": [{"titolo": p.titolo, "giorni": p.giorni} for p in fermi],
        "decisioni_da_rivedere": [
            {"titolo": p.titolo, "stato": p.stato} for p in da_rivedere
        ],
    }


def formatta(brief: Dict[str, object]) -> str:
    """Il brief da leggere. Una cosa sola in testa, il resto sotto."""

    righe: List[str] = []
    prima = brief.get("prima_cosa")

    if not prima:
        if not brief["pagine_totali"]:
            return f"Vault vuoto: {brief['vault']}\nNiente da dire finche' non c'e' dentro qualcosa."
        return "Nessun filo aperto. E' lo stato giusto, non un errore."

    righe.append("LA COSA DA FARE ADESSO")
    righe.append(f"  {prima['titolo']}")
    if prima["blocca"]:
        righe.append(f"  Ne blocca {len(prima['blocca'])}: " + "; ".join(prima["blocca"]))
    if prima["giorni"] is not None:
        righe.append(f"  Ferma da {prima['giorni']} giorni")
    righe.append(f"  -> vault/wiki/{prima['slug']}.md")

    altri = brief.get("altri_aperti") or []
    if altri:
        righe.append("")
        righe.append(f"ALTRI FILI APERTI ({len(altri)})")
        for voce in altri:
            eta = f", {voce['giorni']}g" if voce["giorni"] is not None else ""
            blocco = f", blocca {len(voce['blocca'])}" if voce["blocca"] else ""
            righe.append(f"  - {voce['titolo']}{eta}{blocco}")

    fermi = brief.get("fermi") or []
    if fermi:
        righe.append("")
        righe.append(f"FERMI DA OLTRE {GIORNI_FERMO} GIORNI")
        for voce in fermi:
            righe.append(f"  - {voce['titolo']} ({voce['giorni']}g)")

    revisioni = brief.get("decisioni_da_rivedere") or []
    if revisioni:
        righe.append("")
        righe.append("DECISIONI NON PIU' ATTIVE")
        for voce in revisioni:
            righe.append(f"  - {voce['titolo']} [{voce['stato']}]")

    return "\n".join(righe)

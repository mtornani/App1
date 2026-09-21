"""Test dell'agenzia: stdlib unittest, nessuna rete, nessuna chiave.

Eseguibili ovunque:  python -m unittest agency.tests.test_agency -v
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

from agency import brief, config, decisions, orchestrator, roster, store, tools
from agency import providers
from agency.providers import EchoProvider, ProviderError, build_provider


class ScriptedProvider:
    """Provider finto: risponde con una coda di battute predefinite.

    Serve a testare le topologie in modo deterministico, senza toccare la rete.
    """

    name = "scripted"
    model = "scripted"

    def __init__(self, replies: List[str]) -> None:
        self.replies = list(replies)
        self.calls: List[Dict[str, str]] = []

    def complete(self, system: str, messages, max_tokens: int) -> str:
        self.calls.append({"system": system, "prompt": messages[-1]["content"]})
        return self.replies.pop(0) if self.replies else "DONE"


class TempStateTestCase(unittest.TestCase):
    """Isola lo stato in una cartella temporanea: i test non sporcano il repo."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self._saved = (config.STATE_DIR, config.MISSIONS_DIR, config.RUNS_DIR,
                       config.INDEX_FILE, config.OUTPUT_DIR, config.VAULT_DIR)
        config.STATE_DIR = base
        config.MISSIONS_DIR = base / "missions"
        config.RUNS_DIR = base / "runs"
        config.INDEX_FILE = base / "index.json"
        config.OUTPUT_DIR = base / "output"
        config.VAULT_DIR = base / "vault"
        (config.VAULT_DIR / "wiki").mkdir(parents=True, exist_ok=True)
        (config.VAULT_DIR / "raw").mkdir(parents=True, exist_ok=True)
        config.ensure_dirs()

    def tearDown(self) -> None:
        (config.STATE_DIR, config.MISSIONS_DIR, config.RUNS_DIR,
         config.INDEX_FILE, config.OUTPUT_DIR, config.VAULT_DIR) = self._saved
        self._tmp.cleanup()


class TestStore(TempStateTestCase):
    def test_slugify_normalizza_accenti_e_simboli(self) -> None:
        self.assertEqual(store.slugify("Perché Però! 2026"), "perche-pero-2026")
        self.assertEqual(store.slugify(""), "mission")

    def test_mission_id_ha_formato_ordinabile(self) -> None:
        mission_id = store.new_mission_id("Shortlist oriundi")
        self.assertRegex(mission_id, r"^m-\d{8}-\d{6}-shortlist-oriundi$")

    def test_id_duplicato_riceve_un_suffisso(self) -> None:
        # Stesso obiettivo inviato due volte nello stesso secondo: la seconda
        # missione non deve sovrascrivere la prima.
        first = store.create_mission("Stesso obiettivo")
        second = store.create_mission("Stesso obiettivo")
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(len(store.list_missions()), 2)

    def test_timestamp_ha_precisione_al_millisecondo(self) -> None:
        self.assertRegex(store.utc_now(), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

    def test_create_and_load_roundtrip(self) -> None:
        created = store.create_mission("Analizza pressing", topology="swarm", agents=["analyst"])
        loaded = store.load_mission(created["id"])
        self.assertEqual(loaded["objective"], "Analizza pressing")
        self.assertEqual(loaded["status"], "pending")
        self.assertEqual(loaded["agents"], ["analyst"])

    def test_pending_e_fifo(self) -> None:
        first = store.create_mission("Prima")
        second = store.create_mission("Seconda")
        queue = store.pending_missions()
        self.assertEqual([m["id"] for m in queue], [first["id"], second["id"]])

    def test_pending_rispetta_il_limite(self) -> None:
        for index in range(4):
            store.create_mission(f"Missione {index}")
        self.assertEqual(len(store.pending_missions(limit=2)), 2)

    def test_index_conta_per_stato(self) -> None:
        done = store.create_mission("Chiusa")
        done["status"] = "done"
        store.save_mission(done)
        store.create_mission("Aperta")
        index = store.rebuild_index()
        self.assertEqual(index["counts"]["done"], 1)
        self.assertEqual(index["counts"]["pending"], 1)
        self.assertEqual(len(index["missions"]), 2)

    def test_index_non_si_riscrive_se_nulla_e_cambiato(self) -> None:
        # Senza questo, il workflow committerebbe una riga ogni mezz'ora solo
        # perche' cambia l'orario, e i commit veri annegherebbero.
        store.create_mission("Una")
        store.rebuild_index()
        prima = config.INDEX_FILE.read_text(encoding="utf-8")
        store.rebuild_index()
        self.assertEqual(config.INDEX_FILE.read_text(encoding="utf-8"), prima)

    def test_index_si_riscrive_quando_cambia_qualcosa(self) -> None:
        store.create_mission("Una")
        store.rebuild_index()
        prima = config.INDEX_FILE.read_text(encoding="utf-8")
        store.create_mission("Due")
        store.rebuild_index()
        self.assertNotEqual(config.INDEX_FILE.read_text(encoding="utf-8"), prima)

    def test_file_corrotto_non_blocca_la_lista(self) -> None:
        store.create_mission("Valida")
        (config.MISSIONS_DIR / "m-rotta.json").write_text("{non json", encoding="utf-8")
        self.assertEqual(len(store.list_missions()), 1)


class TestRoster(unittest.TestCase):
    def test_roster_contiene_i_ruoli_chiave(self) -> None:
        loaded = roster.load_roster()
        for agent_id in ("pm", "researcher", "analyst", "engineer", "writer", "critic"):
            self.assertIn(agent_id, loaded)

    def test_pm_escluso_dai_worker(self) -> None:
        self.assertNotIn("pm", roster.worker_ids())

    def test_agente_inesistente_alza_keyerror(self) -> None:
        with self.assertRaises(KeyError):
            roster.get_agent("nessuno")


class TestJsonExtraction(unittest.TestCase):
    def test_estrae_json_da_blocco_fenced(self) -> None:
        raw = 'Ecco il piano:\n```json\n{"plan": [{"agent": "writer", "task": "x"}]}\n```\nBuon lavoro!'
        parsed = orchestrator.Orchestrator._extract_json(raw)
        self.assertEqual(parsed["plan"][0]["agent"], "writer")

    def test_estrae_json_annegato_nella_prosa(self) -> None:
        raw = 'Certo. {"plan": []} Fammi sapere.'
        self.assertEqual(orchestrator.Orchestrator._extract_json(raw), {"plan": []})

    def test_restituisce_none_se_non_ce_json(self) -> None:
        self.assertIsNone(orchestrator.Orchestrator._extract_json("nessun json qui"))


class TestTopologie(TempStateTestCase):
    def test_solo_usa_un_solo_agente(self) -> None:
        mission = store.create_mission("Riassumi", topology="solo", agents=["writer"])
        provider = ScriptedProvider(["Sintesi finale."])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["steps"], 1)
        self.assertEqual(run["transcript"][0]["agent"], "writer")
        self.assertEqual(run["deliverable"], "Sintesi finale.")

    def test_team_segue_il_piano_del_pm(self) -> None:
        mission = store.create_mission("Costruisci shortlist", topology="team")
        provider = ScriptedProvider([
            '```json\n{"plan": [{"agent": "researcher", "task": "Raccogli"},'
            '{"agent": "writer", "task": "Scrivi"}]}\n```',
            "Fatti raccolti.",
            "Report finale.",
        ])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual([turn["agent"] for turn in run["transcript"]], ["researcher", "writer"])
        self.assertEqual(run["deliverable"], "Report finale.")

    def test_team_scarta_agenti_inesistenti_dal_piano(self) -> None:
        mission = store.create_mission("Obiettivo", topology="team")
        provider = ScriptedProvider([
            '{"plan": [{"agent": "fantasma", "task": "x"}, {"agent": "critic", "task": "Verifica"}]}',
            "VERDETTO: OK",
        ])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual([turn["agent"] for turn in run["transcript"]], ["critic"])

    def test_team_usa_il_piano_di_riserva_se_il_pm_non_produce_json(self) -> None:
        mission = store.create_mission("Obiettivo", topology="team")
        provider = ScriptedProvider(["Non mi va di rispondere in JSON.", "Fatti.", "Report."])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual([turn["agent"] for turn in run["transcript"]], ["researcher", "writer"])

    def test_team_vede_il_lavoro_precedente(self) -> None:
        mission = store.create_mission("Obiettivo", topology="team")
        provider = ScriptedProvider([
            '{"plan": [{"agent": "researcher", "task": "Raccogli"}, {"agent": "writer", "task": "Scrivi"}]}',
            "IMPRONTA-RICERCA",
            "Report.",
        ])
        orchestrator.Orchestrator(provider).run(mission)
        self.assertIn("IMPRONTA-RICERCA", provider.calls[-1]["prompt"])

    def test_swarm_segue_gli_handoff(self) -> None:
        mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
        provider = ScriptedProvider([
            "Fatti raccolti.\nHANDOFF: analyst",
            "Metriche pronte.\nHANDOFF: writer",
            "Deliverable.\nDONE",
        ])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual([turn["agent"] for turn in run["transcript"]],
                         ["researcher", "analyst", "writer"])

    def test_swarm_ignora_handoff_non_consentiti(self) -> None:
        # researcher non puo' passare a engineer: la catena si chiude invece di
        # inventare un percorso non dichiarato nel roster.
        mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
        provider = ScriptedProvider(["Fatti.\nHANDOFF: engineer", "non dovrebbe servire"])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["steps"], 1)

    def test_swarm_si_ferma_al_tetto_dei_passi(self) -> None:
        saved = config.MAX_STEPS
        config.MAX_STEPS = 3
        try:
            mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
            provider = ScriptedProvider(["a\nHANDOFF: analyst", "b\nHANDOFF: writer",
                                         "c\nHANDOFF: critic", "d\nHANDOFF: writer"])
            run = orchestrator.Orchestrator(provider).run(mission)
            self.assertEqual(len(run["transcript"]), 4)  # 3 turni + riga di stop
            self.assertIn("[STOP]", run["transcript"][-1]["output"])
        finally:
            config.MAX_STEPS = saved

    def test_topologia_sconosciuta_e_un_errore(self) -> None:
        mission = store.create_mission("Obiettivo")
        mission["topology"] = "piramide"
        with self.assertRaises(ValueError):
            orchestrator.Orchestrator(ScriptedProvider([])).run(mission)


class TestCicloMissione(TempStateTestCase):
    def test_missione_completata_salva_run_e_deliverable(self) -> None:
        mission = store.create_mission("Obiettivo", topology="solo", agents=["writer"])
        orchestrator.execute_mission(mission["id"], ScriptedProvider(["Esito."]))
        reloaded = store.load_mission(mission["id"])
        self.assertEqual(reloaded["status"], "done")
        self.assertEqual(reloaded["deliverable"], "Esito.")
        self.assertIsNotNone(store.load_run(mission["id"]))
        self.assertTrue(config.INDEX_FILE.exists())

    def test_missione_fallita_registra_errore(self) -> None:
        class Broken:
            name = "broken"
            model = "broken"

            def complete(self, *_args, **_kwargs):
                raise ProviderError("chiave scaduta")

        mission = store.create_mission("Obiettivo", topology="solo", agents=["writer"])
        with self.assertRaises(ProviderError):
            orchestrator.execute_mission(mission["id"], Broken())
        reloaded = store.load_mission(mission["id"])
        self.assertEqual(reloaded["status"], "failed")
        self.assertIn("chiave scaduta", reloaded["error"])


class TestParsingChiamate(unittest.TestCase):
    def test_riconosce_una_chiamata(self) -> None:
        call = tools.parse_call('Scarico la fonte.\nTOOL: fetch\n{"url": "https://it.wikipedia.org/x"}')
        self.assertEqual(call[0], "fetch")
        self.assertEqual(call[1]["url"], "https://it.wikipedia.org/x")

    def test_prende_lultima_chiamata(self) -> None:
        text = 'TOOL: fetch\n{"url": "https://a.org"}\nripenso\nTOOL: fetch\n{"url": "https://b.org"}'
        self.assertEqual(tools.parse_call(text)[1]["url"], "https://b.org")

    def test_nessuna_chiamata_restituisce_none(self) -> None:
        self.assertIsNone(tools.parse_call("Ecco la risposta finale, nessuno strumento."))

    def test_json_rotto_e_segnalato_non_esplode(self) -> None:
        name, args = tools.parse_call('TOOL: fetch\n{"url": non chiuso}')
        self.assertEqual(name, "fetch")
        self.assertIn("__json_error__", args)


class TestProtocolloContenutoLungo(unittest.TestCase):
    """Le tre forme di chiamata, e il caso che ha fatto fallire il primo giro reale."""

    def test_blocco_di_contenuto_fuori_dal_json(self) -> None:
        # Un documento dentro una stringa JSON costa escape ed e' fragile.
        testo = ('Salvo il report.\nTOOL: write_file\n{"path": "report.md"}\n'
                 '<<<CONTENT\n# Titolo\n\nRiga con "virgolette" e a capo.\nCONTENT')
        nome, args = tools.parse_call(testo)
        self.assertEqual(nome, "write_file")
        self.assertEqual(args["path"], "report.md")
        self.assertIn('"virgolette"', args["content"])
        self.assertTrue(args["content"].startswith("# Titolo"))

    def test_il_blocco_vince_sul_campo_json(self) -> None:
        testo = ('TOOL: write_file\n{"path": "a.md", "content": "vecchio"}\n'
                 '<<<CONTENT\nnuovo\nCONTENT')
        _, args = tools.parse_call(testo)
        self.assertEqual(args["content"], "nuovo")

    def test_chiamata_troncata_riconosciuta(self) -> None:
        # E' esattamente cio' che e' successo il 2026-09-21: la risposta del
        # writer e' finita a meta' JSON e la chiamata e' passata per prosa.
        testo = 'TOOL: write_file\n{"path": "r.md", "content": "inizio ma non fin'
        nome, args = tools.parse_call(testo)
        self.assertEqual(nome, "write_file")
        self.assertIn("__truncated__", args)

    def test_troncata_torna_allagente_con_istruzioni(self) -> None:
        ctx = tools.build_context("m-test")
        result = tools.execute("write_file", {"__truncated__": True}, ctx, ["write_file"])
        self.assertFalse(result.ok)
        self.assertIn("CONTENT", result.output)

    def test_forma_classica_ancora_valida(self) -> None:
        nome, args = tools.parse_call('TOOL: fetch\n{"url": "https://x.org"}')
        self.assertEqual((nome, args["url"]), ("fetch", "https://x.org"))

    def test_strip_toglie_anche_il_blocco(self) -> None:
        testo = ('Sintesi finale.\nTOOL: write_file\n{"path": "a.md"}\n'
                 '<<<CONTENT\ncorpo\nCONTENT')
        self.assertEqual(tools.strip_calls(testo), "Sintesi finale.")

    def test_testo_normale_non_e_una_chiamata(self) -> None:
        self.assertIsNone(tools.parse_call("Parlo di TOOL come concetto, senza chiamarlo."))


class TestPianoDelPm(TempStateTestCase):
    def test_il_pm_vede_gli_strumenti_di_ogni_agente(self) -> None:
        # Senza questa informazione assegna passi ineseguibili: al primo giro
        # reale ha chiesto al researcher di salvare un file.
        mission = store.create_mission("Obiettivo", topology="team")
        provider = ScriptedProvider(['{"plan": [{"agent": "writer", "task": "Scrivi"}]}', "Fatto."])
        orchestrator.Orchestrator(provider).run(mission)
        prompt_pm = provider.calls[0]["prompt"]
        # Ogni ruolo operativo compare con i suoi strumenti effettivi.
        for agente in roster.worker_ids():
            spec = roster.get_agent(agente)
            self.assertIn(f"{spec.id}: {spec.title} [puo' usare: " + ", ".join(spec.tools),
                          prompt_pm)
        # E il vincolo esplicito che impedisce i passi ineseguibili.
        self.assertIn("Chi non ha write_file non puo' produrre file", prompt_pm)


class TestToolFetch(TempStateTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.ctx = tools.build_context("m-test")

    def _run(self, args):
        return tools.execute("fetch", args, self.ctx, ["fetch"])

    def test_rifiuta_schemi_non_https(self) -> None:
        result = self._run({"url": "http://it.wikipedia.org/x"})
        self.assertFalse(result.ok)
        self.assertIn("https", result.output)

    def test_rifiuta_file_url(self) -> None:
        self.assertFalse(self._run({"url": "file:///etc/passwd"}).ok)

    def test_rifiuta_dominio_fuori_allowlist(self) -> None:
        result = self._run({"url": "https://esempio-non-consentito.test/x"})
        self.assertFalse(result.ok)
        self.assertIn("allowlist", result.output)

    def test_allowlist_copre_i_sottodomini(self) -> None:
        self.assertTrue(tools._domain_allowed("it.wikipedia.org"))
        self.assertTrue(tools._domain_allowed("wikipedia.org"))
        self.assertFalse(tools._domain_allowed("wikipedia.org.evil.test"))

    def test_indirizzi_privati_bloccati(self) -> None:
        # Difesa SSRF: in CI il runner vede servizi interni.
        self.assertFalse(tools._host_is_public("localhost"))

    def test_allowlist_vale_anche_passando_da_jina(self) -> None:
        # Il controllo sta sull'URL di destinazione, non su r.jina.ai:
        # cambiare trasporto non deve aprire un varco.
        saved = config.FETCH_VIA
        config.FETCH_VIA = "jina"
        try:
            result = self._run({"url": "https://esempio-non-consentito.test/x"})
            self.assertFalse(result.ok)
            self.assertIn("allowlist", result.output)
        finally:
            config.FETCH_VIA = saved

    def test_https_obbligatorio_anche_passando_da_jina(self) -> None:
        saved = config.FETCH_VIA
        config.FETCH_VIA = "jina"
        try:
            self.assertFalse(self._run({"url": "http://it.wikipedia.org/x"}).ok)
        finally:
            config.FETCH_VIA = saved

    def test_html_diventa_testo_leggibile(self) -> None:
        parser = tools._TextExtractor()
        parser.feed("<html><head><title>x</title></head><body><script>var a=1</script>"
                    "<h1>Titolo</h1><p>Primo paragrafo.</p><p>Secondo.</p></body></html>")
        text = parser.text()
        self.assertIn("Titolo", text)
        self.assertIn("Primo paragrafo.", text)
        self.assertNotIn("var a=1", text)


class TestAdattatoreWikipedia(unittest.TestCase):
    def test_riscrive_larticolo_nellapi(self) -> None:
        rewritten = tools._wikipedia_plaintext("https://it.wikipedia.org/wiki/Aldo_Simoncini")
        self.assertIn("/w/api.php?", rewritten)
        self.assertIn("explaintext=1", rewritten)
        self.assertIn("Aldo+Simoncini", rewritten)

    def test_non_tocca_url_non_wikipedia(self) -> None:
        self.assertIsNone(tools._wikipedia_plaintext("https://github.com/statsbomb/open-data"))

    def test_non_tocca_url_gia_api(self) -> None:
        self.assertIsNone(tools._wikipedia_plaintext("https://it.wikipedia.org/w/api.php?action=query"))

    def test_estrae_il_testo_dalla_risposta(self) -> None:
        body = '{"query": {"pages": {"42": {"extract": "Testo articolo."}}}}'
        self.assertEqual(tools._unwrap_wikipedia(body), "Testo articolo.")

    def test_risposta_inattesa_non_esplode(self) -> None:
        self.assertIsNone(tools._unwrap_wikipedia("non json"))
        self.assertIsNone(tools._unwrap_wikipedia('{"query": {}}'))


class TestInstradamentoJina(unittest.TestCase):
    """Quale percorso prende fetch. Deterministico, nessuna rete."""

    def setUp(self) -> None:
        self._via, self._key = config.FETCH_VIA, config.JINA_API_KEY

    def tearDown(self) -> None:
        config.FETCH_VIA, config.JINA_API_KEY = self._via, self._key

    def test_auto_usa_jina_solo_con_la_chiave(self) -> None:
        config.FETCH_VIA = "auto"
        config.JINA_API_KEY = ""
        self.assertFalse(tools._usa_jina())
        config.JINA_API_KEY = "chiave"
        self.assertTrue(tools._usa_jina())

    def test_direct_vince_anche_con_la_chiave(self) -> None:
        # Mandare l'URL a un terzo deve restare una scelta revocabile.
        config.FETCH_VIA = "direct"
        config.JINA_API_KEY = "chiave"
        self.assertFalse(tools._usa_jina())

    def test_jina_forzabile_senza_chiave(self) -> None:
        config.FETCH_VIA = "jina"
        config.JINA_API_KEY = ""
        self.assertTrue(tools._usa_jina())


class TestToolFile(TempStateTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.ctx = tools.build_context("m-test")

    def test_scrive_e_registra_lartefatto(self) -> None:
        result = tools.execute("write_file", {"path": "report.md", "content": "# Esito"},
                               self.ctx, ["write_file"])
        self.assertTrue(result.ok)
        self.assertEqual(self.ctx.artifacts, ["report.md"])
        self.assertEqual((self.ctx.output_dir / "report.md").read_text(encoding="utf-8"), "# Esito")

    def test_scrive_in_sottocartella(self) -> None:
        result = tools.execute("write_file", {"path": "dati/players.csv", "content": "a,b\n1,2"},
                               self.ctx, ["write_file"])
        self.assertTrue(result.ok)
        self.assertTrue((self.ctx.output_dir / "dati" / "players.csv").exists())

    def test_blocca_il_traversal(self) -> None:
        result = tools.execute("write_file", {"path": "../../fuori.md", "content": "x"},
                               self.ctx, ["write_file"])
        self.assertFalse(result.ok)
        self.assertFalse((config.OUTPUT_DIR.parent / "fuori.md").exists())

    def test_blocca_il_percorso_assoluto(self) -> None:
        self.assertFalse(tools.execute("write_file", {"path": "/tmp/fuori.md", "content": "x"},
                                       self.ctx, ["write_file"]).ok)

    def test_rifiuta_contenuto_non_stringa(self) -> None:
        self.assertFalse(tools.execute("write_file", {"path": "a.md", "content": {"x": 1}},
                                       self.ctx, ["write_file"]).ok)

    def test_tetto_sulla_dimensione(self) -> None:
        saved = config.WRITE_MAX_BYTES
        config.WRITE_MAX_BYTES = 10
        try:
            self.assertFalse(tools.execute("write_file", {"path": "a.md", "content": "x" * 50},
                                           self.ctx, ["write_file"]).ok)
        finally:
            config.WRITE_MAX_BYTES = saved

    def test_tetto_sul_numero_di_file(self) -> None:
        saved = config.MAX_ARTIFACTS
        config.MAX_ARTIFACTS = 2
        try:
            for index in range(2):
                tools.execute("write_file", {"path": f"f{index}.md", "content": "x"},
                              self.ctx, ["write_file"])
            self.assertFalse(tools.execute("write_file", {"path": "f9.md", "content": "x"},
                                           self.ctx, ["write_file"]).ok)
        finally:
            config.MAX_ARTIFACTS = saved

    def test_legge_un_file_del_repo(self) -> None:
        result = tools.execute("read_file", {"path": "agency/agents/writer.json"},
                               self.ctx, ["read_file"])
        self.assertTrue(result.ok)
        self.assertIn("write_file", result.output)

    def test_legge_anche_gli_artefatti_della_missione(self) -> None:
        # Senza questo il critic non puo' verificare cio' che il team produce.
        # Il 2026-09-21 ha bocciato un report che esisteva, non potendolo vedere.
        tools.execute("write_file", {"path": "report.md", "content": "# Esito"},
                      self.ctx, ["write_file"])
        result = tools.execute("read_file", {"path": "report.md"}, self.ctx, ["read_file"])
        self.assertTrue(result.ok)
        self.assertIn("# Esito", result.output)
        self.assertIn("missione", result.output)

    def test_il_repository_ha_la_precedenza(self) -> None:
        result = tools.execute("read_file", {"path": "agency/agents/writer.json"},
                               self.ctx, ["read_file"])
        self.assertTrue(result.ok)
        self.assertIn("repository", result.output)

    def test_file_inesistente_dice_dove_ha_cercato(self) -> None:
        result = tools.execute("read_file", {"path": "mai-scritto.md"},
                               self.ctx, ["read_file"])
        self.assertFalse(result.ok)
        self.assertIn("artefatti", result.output)

    def test_non_legge_estensioni_non_ammesse(self) -> None:
        self.assertFalse(tools.execute("read_file", {"path": "agency/web/icon.svg"},
                                       self.ctx, ["read_file"]).ok)

    def test_non_legge_dentro_git(self) -> None:
        self.assertFalse(tools.execute("read_file", {"path": ".git/config"},
                                       self.ctx, ["read_file"]).ok)

    def test_permessi_per_ruolo(self) -> None:
        # Il writer non tocca la rete, nemmeno se lo chiede.
        result = tools.execute("fetch", {"url": "https://it.wikipedia.org/x"},
                               self.ctx, ["write_file"])
        self.assertFalse(result.ok)
        self.assertIn("permesso", result.output)

    def test_tool_inesistente(self) -> None:
        self.assertFalse(tools.execute("telepatia", {}, self.ctx, ["write_file"]).ok)

    def test_ogni_chiamata_finisce_nel_log(self) -> None:
        tools.execute("write_file", {"path": "a.md", "content": "x"}, self.ctx, ["write_file"])
        tools.execute("write_file", {"path": "../b.md", "content": "x"}, self.ctx, ["write_file"])
        self.assertEqual(len(self.ctx.calls), 2)
        self.assertEqual([c["ok"] for c in self.ctx.calls], [True, False])


class TestCicloStrumenti(TempStateTestCase):
    def test_lagente_usa_il_tool_e_prosegue(self) -> None:
        mission = store.create_mission("Produci un report", topology="solo", agents=["writer"])
        provider = ScriptedProvider([
            'Salvo il file.\nTOOL: write_file\n{"path": "report.md", "content": "# Report\\n\\nEsito."}',
            "Fatto: report.md salvato.",
        ])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["artifacts"], ["report.md"])
        self.assertEqual(run["deliverable"], "Fatto: report.md salvato.")
        self.assertEqual(run["transcript"][0]["tool_calls"][0]["tool"], "write_file")

    def test_errore_di_tool_torna_allagente_senza_fermare_la_missione(self) -> None:
        mission = store.create_mission("Produci", topology="solo", agents=["writer"])
        provider = ScriptedProvider([
            'TOOL: write_file\n{"path": "../fuori.md", "content": "x"}',
            "Corretto, salvo dentro la cartella.",
        ])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["artifacts"], [])
        self.assertFalse(run["tool_calls"][0]["ok"])
        self.assertEqual(run["deliverable"], "Corretto, salvo dentro la cartella.")

    def test_tetto_sulle_chiamate_chiude_il_turno(self) -> None:
        saved = config.MAX_TOOL_CALLS
        config.MAX_TOOL_CALLS = 2
        try:
            mission = store.create_mission("Produci", topology="solo", agents=["writer"])
            # Un agente che chiama all'infinito: al tetto gli si chiede la risposta.
            provider = ScriptedProvider(['TOOL: write_file\n{"path": "a.md", "content": "x"}'] * 2
                                        + ["Chiudo qui."])
            run = orchestrator.Orchestrator(provider).run(mission)
            self.assertEqual(len(run["tool_calls"]), 2)
            self.assertEqual(run["deliverable"], "Chiudo qui.")
        finally:
            config.MAX_TOOL_CALLS = saved

    def test_protocollo_ripulito_dalla_risposta_finale(self) -> None:
        # Se l'agente insiste con una riga TOOL dopo il tetto, quella riga non
        # deve finire nel deliverable.
        saved = config.MAX_TOOL_CALLS
        config.MAX_TOOL_CALLS = 1
        try:
            mission = store.create_mission("Produci", topology="solo", agents=["writer"])
            provider = ScriptedProvider([
                'TOOL: write_file\n{"path": "a.md", "content": "x"}',
                'Sintesi finale.\nTOOL: write_file\n{"path": "b.md", "content": "y"}',
            ])
            run = orchestrator.Orchestrator(provider).run(mission)
            self.assertEqual(run["deliverable"], "Sintesi finale.")
            self.assertNotIn("TOOL:", run["deliverable"])
        finally:
            config.MAX_TOOL_CALLS = saved

    def test_agente_senza_tool_ignora_il_protocollo(self) -> None:
        # Il pm non ha strumenti: una riga TOOL nel suo output e' solo testo.
        mission = store.create_mission("Produci", topology="team")
        provider = ScriptedProvider([
            'TOOL: write_file\n{"path": "a.md", "content": "x"}',
            "Fatti.", "Report.",
        ])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["artifacts"], [])

    def test_missione_completata_espone_gli_artefatti(self) -> None:
        mission = store.create_mission("Produci", topology="solo", agents=["writer"])
        provider = ScriptedProvider([
            'TOOL: write_file\n{"path": "report.md", "content": "ok"}',
            "Salvato.",
        ])
        orchestrator.execute_mission(mission["id"], provider)
        self.assertEqual(store.load_mission(mission["id"])["artifacts"], ["report.md"])
        index = store.rebuild_index()
        self.assertEqual(index["missions"][0]["artifacts"], ["report.md"])


class TestProviders(unittest.TestCase):
    def test_echo_e_offline_e_deterministico(self) -> None:
        provider = EchoProvider()
        first = provider.complete("ruolo", [{"role": "user", "content": "ciao"}], 100)
        second = provider.complete("ruolo", [{"role": "user", "content": "ciao"}], 100)
        self.assertEqual(first, second)

    def test_echo_restituisce_un_piano_valido_per_il_pm(self) -> None:
        raw = EchoProvider().complete("Sei il Project Manager", [{"role": "user", "content": "x"}], 100)
        plan = orchestrator.Orchestrator._extract_json(raw)
        self.assertTrue(plan["plan"])

    def test_provider_sconosciuto_alza_errore(self) -> None:
        with self.assertRaises(ProviderError):
            build_provider("telepatia")

    def test_zai_senza_chiave_alza_errore(self) -> None:
        saved = config.ZAI_API_KEY
        config.ZAI_API_KEY = ""
        try:
            with self.assertRaises(ProviderError):
                build_provider("zai")
        finally:
            config.ZAI_API_KEY = saved

    def test_zai_usa_endpoint_e_modello_attesi(self) -> None:
        saved = config.ZAI_API_KEY
        config.ZAI_API_KEY = "chiave-finta"
        try:
            provider = build_provider("zai")
        finally:
            config.ZAI_API_KEY = saved
        self.assertEqual(provider.name, "zai")
        self.assertEqual(provider.url, "https://api.z.ai/api/paas/v4/chat/completions")
        self.assertEqual(provider.model, "glm-5.3")
        # GLM-5.3 ragiona sempre: lo sforzo va passato esplicitamente.
        self.assertIn("reasoning_effort", provider.extra_body)


class TestDecisioniJev(TempStateTestCase):
    """L'instradamento tipizzato. Nessuna rete: la scelta viene sostituita."""

    def setUp(self) -> None:
        super().setUp()
        self._chiave = config.TYPESAFE_API_KEY
        self._scegli = decisions.scegli

    def tearDown(self) -> None:
        config.TYPESAFE_API_KEY = self._chiave
        decisions.scegli = self._scegli
        super().tearDown()

    def _finge(self, valore, confidenza):
        config.TYPESAFE_API_KEY = "chiave-finta"
        decisions.scegli = lambda *a, **k: decisions.Scelta(valore, confidenza, {})

    def test_senza_chiave_non_si_usa(self) -> None:
        config.TYPESAFE_API_KEY = ""
        self.assertFalse(decisions.disponibile())
        self.assertIsNone(decisions.scegli("stato", "domanda", {"a": "x", "b": "y"}))

    def test_intenzione_esplicita_vince_su_jev(self) -> None:
        # Se l'agente ha detto chiaramente dove vuole andare, non si discute.
        self._finge("writer", 1.0)
        mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
        provider = ScriptedProvider(["Fatti.\nHANDOFF: analyst", "Metriche.\nDONE"])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual([t["agent"] for t in run["transcript"]], ["researcher", "analyst"])

    def test_jev_instrada_quando_il_testo_e_ambiguo(self) -> None:
        # Nessun HANDOFF valido: prima la catena si chiudeva, ora prosegue.
        self._finge("analyst", 0.9)
        mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
        provider = ScriptedProvider(["Fatti raccolti, ma non so chi debba continuare.",
                                     "Metriche pronte.\nDONE"])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual([t["agent"] for t in run["transcript"]], ["researcher", "analyst"])
        self.assertEqual(run["transcript"][0]["routing"]["da"], "jev")

    def test_sotto_soglia_si_chiude_invece_di_indovinare(self) -> None:
        self._finge("analyst", 0.2)
        mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
        provider = ScriptedProvider(["Testo ambiguo.", "non dovrebbe servire"])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["steps"], 1)
        self.assertEqual(run["transcript"][0]["routing"]["confidenza"], 0.2)

    def test_concludi_chiude_la_catena(self) -> None:
        self._finge("concludi", 0.95)
        mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
        provider = ScriptedProvider(["Ho finito ma non l'ho scritto nel formato giusto."])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["steps"], 1)

    def test_scelta_fuori_dalle_opzioni_e_scartata(self) -> None:
        self._finge("engineer", 0.99)  # non raggiungibile da researcher
        mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
        provider = ScriptedProvider(["Testo ambiguo."])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["steps"], 1)

    def test_senza_jev_il_comportamento_e_quello_di_prima(self) -> None:
        config.TYPESAFE_API_KEY = ""
        mission = store.create_mission("Obiettivo", topology="swarm", agents=["researcher"])
        provider = ScriptedProvider(["Testo ambiguo.", "non dovrebbe servire"])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["steps"], 1)
        self.assertNotIn("routing", run["transcript"][0])

    def test_soglia_di_confidenza(self) -> None:
        alta = decisions.Scelta("a", 0.9, {})
        bassa = decisions.Scelta("a", 0.1, {})
        self.assertTrue(alta.sicura)
        self.assertFalse(bassa.sicura)


class TestVault(TempStateTestCase):
    """Il vault e' memoria persistente: le zone di scrittura sono il contratto."""

    def setUp(self) -> None:
        super().setUp()
        self.ctx = tools.build_context("m-test")
        (config.VAULT_DIR / "raw" / "fonte.md").write_text("Testo della fonte.", encoding="utf-8")
        (config.VAULT_DIR / "AGENTS.md").write_text("# Schema\nRegole.", encoding="utf-8")

    def _run(self, name, args):
        return tools.execute(name, args, self.ctx,
                             ["vault_list", "vault_read", "vault_write"])

    def test_scrive_una_pagina_della_wiki(self) -> None:
        result = self._run("vault_write", {"path": "wiki/decisione.md", "content": "# Decisione"})
        self.assertTrue(result.ok)
        self.assertEqual((config.VAULT_DIR / "wiki" / "decisione.md").read_text(encoding="utf-8"),
                         "# Decisione\n")
        self.assertEqual(self.ctx.vault_pages, ["wiki/decisione.md"])

    def test_raw_e_immutabile(self) -> None:
        # La fonte dell'umano non si tocca: e' la regola che tiene in piedi tutto.
        result = self._run("vault_write", {"path": "raw/fonte.md", "content": "riscritto"})
        self.assertFalse(result.ok)
        self.assertIn("immutabile", result.output)
        self.assertEqual((config.VAULT_DIR / "raw" / "fonte.md").read_text(encoding="utf-8"),
                         "Testo della fonte.")

    def test_raw_resta_leggibile(self) -> None:
        result = self._run("vault_read", {"path": "raw/fonte.md"})
        self.assertTrue(result.ok)
        self.assertIn("Testo della fonte.", result.output)

    def test_non_scrive_fuori_dalle_zone_consentite(self) -> None:
        self.assertFalse(self._run("vault_write", {"path": "AGENTS.md", "content": "x"}).ok)
        self.assertFalse(self._run("vault_write", {"path": "altro/x.md", "content": "x"}).ok)

    def test_index_e_log_sono_scrivibili(self) -> None:
        self.assertTrue(self._run("vault_write", {"path": "index.md", "content": "# Indice"}).ok)
        self.assertTrue(self._run("vault_write", {"path": "log.md", "content": "# Log"}).ok)

    def test_append_non_sovrascrive(self) -> None:
        # log.md e' append-only per contratto: la storia non si riscrive.
        self._run("vault_write", {"path": "log.md", "content": "## [2026-01-01] init"})
        self._run("vault_write", {"path": "log.md", "content": "## [2026-01-02] ingest", "append": True})
        testo = (config.VAULT_DIR / "log.md").read_text(encoding="utf-8")
        self.assertIn("[2026-01-01]", testo)
        self.assertIn("[2026-01-02]", testo)

    def test_blocca_traversal_e_assoluti(self) -> None:
        self.assertFalse(self._run("vault_write", {"path": "../fuori.md", "content": "x"}).ok)
        self.assertFalse(self._run("vault_write", {"path": "/tmp/fuori.md", "content": "x"}).ok)

    def test_rifiuta_estensioni_binarie(self) -> None:
        self.assertFalse(self._run("vault_write", {"path": "wiki/a.png", "content": "x"}).ok)

    def test_elenca_le_pagine(self) -> None:
        self._run("vault_write", {"path": "wiki/uno.md", "content": "a"})
        result = self._run("vault_list", {})
        self.assertTrue(result.ok)
        self.assertIn("wiki/uno.md", result.output)
        self.assertIn("raw/fonte.md", result.output)

    def test_pagina_inesistente_indirizza_alla_lista(self) -> None:
        result = self._run("vault_read", {"path": "wiki/mai-scritta.md"})
        self.assertFalse(result.ok)
        self.assertIn("vault_list", result.output)

    def test_librarian_ha_i_permessi_giusti(self) -> None:
        librarian = roster.get_agent("librarian")
        self.assertEqual(sorted(librarian.tools), ["vault_list", "vault_read", "vault_write"])

    def test_critic_legge_il_vault_ma_non_ci_scrive(self) -> None:
        critic = roster.get_agent("critic")
        self.assertIn("vault_read", critic.tools)
        self.assertNotIn("vault_write", critic.tools)

    def test_missione_riporta_le_pagine_toccate(self) -> None:
        mission = store.create_mission("Ingest", topology="solo", agents=["librarian"])
        provider = ScriptedProvider([
            'TOOL: vault_write\n{"path": "wiki/nuova.md", "content": "# Nuova"}',
            "Pagina scritta e indice aggiornato.",
        ])
        run = orchestrator.Orchestrator(provider).run(mission)
        self.assertEqual(run["vault_pages"], ["wiki/nuova.md"])


class TestBrief(TempStateTestCase):
    """Il brief e' deterministico: se sbaglia, sbaglia sempre e si vede."""

    def _pagina(self, slug, tipo="thread", stato="aperto", updated="2026-09-21",
                blocked_by=None, titolo=None):
        righe = ["---", f"type: {tipo}", f"title: {titolo or slug}",
                 f"updated: {updated}", f"status: {stato}"]
        if blocked_by:
            righe.append("blocked_by: [" + ", ".join(blocked_by) + "]")
        righe += ["---", "", "Corpo."]
        (config.VAULT_DIR / "wiki" / f"{slug}.md").write_text(
            "\n".join(righe), encoding="utf-8")

    def test_vault_vuoto_lo_dice(self) -> None:
        testo = brief.formatta(brief.componi(config.VAULT_DIR))
        self.assertIn("vuoto", testo.lower())

    def test_il_bloccante_viene_per_primo(self) -> None:
        # Due fili aspettano il terzo: il terzo e' la cosa da fare adesso,
        # anche se e' stato scritto per ultimo.
        self._pagina("bloccante", titolo="Il bloccante")
        self._pagina("attesa-uno", titolo="Attesa uno", blocked_by=["bloccante"])
        self._pagina("attesa-due", titolo="Attesa due", blocked_by=["bloccante"])
        dati = brief.componi(config.VAULT_DIR)
        self.assertEqual(dati["prima_cosa"]["slug"], "bloccante")
        self.assertEqual(len(dati["prima_cosa"]["blocca"]), 2)

    def test_un_filo_bloccato_non_e_la_prima_cosa(self) -> None:
        self._pagina("vecchio-ma-bloccato", updated="2025-01-01",
                     blocked_by=["recente"], titolo="Vecchio ma bloccato")
        self._pagina("recente", titolo="Recente")
        dati = brief.componi(config.VAULT_DIR)
        self.assertEqual(dati["prima_cosa"]["slug"], "recente")

    def test_a_parita_vince_il_piu_fermo(self) -> None:
        self._pagina("fresco", updated="2026-09-20", titolo="Fresco")
        self._pagina("fermo", updated="2026-06-01", titolo="Fermo")
        dati = brief.componi(config.VAULT_DIR)
        self.assertEqual(dati["prima_cosa"]["slug"], "fermo")

    def test_i_chiusi_non_compaiono(self) -> None:
        self._pagina("chiuso", stato="chiuso", titolo="Chiuso")
        self._pagina("aperto", titolo="Aperto")
        dati = brief.componi(config.VAULT_DIR)
        self.assertEqual(dati["prima_cosa"]["slug"], "aperto")
        self.assertEqual(dati["altri_aperti"], [])

    def test_segnala_i_fermi_oltre_la_soglia(self) -> None:
        self._pagina("vecchio", updated="2026-01-01", titolo="Vecchio")
        dati = brief.componi(config.VAULT_DIR)
        self.assertEqual(len(dati["fermi"]), 1)

    def test_segnala_le_decisioni_non_piu_attive(self) -> None:
        self._pagina("scelta", tipo="decision", stato="da rivedere", titolo="Scelta")
        dati = brief.componi(config.VAULT_DIR)
        self.assertEqual(dati["decisioni_da_rivedere"][0]["stato"], "da rivedere")

    def test_frontmatter_rotto_non_fa_esplodere_niente(self) -> None:
        (config.VAULT_DIR / "wiki" / "rotta.md").write_text(
            "niente frontmatter qui", encoding="utf-8")
        self._pagina("buona", titolo="Buona")
        dati = brief.componi(config.VAULT_DIR)
        self.assertEqual(dati["prima_cosa"]["slug"], "buona")

    def test_dipendenza_verso_pagina_inesistente_e_ignorata(self) -> None:
        self._pagina("solo", blocked_by=["mai-scritta"], titolo="Solo")
        dati = brief.componi(config.VAULT_DIR)
        self.assertEqual(dati["prima_cosa"]["slug"], "solo")

    def test_nessun_filo_aperto_e_uno_stato_valido(self) -> None:
        self._pagina("finito", stato="chiuso", titolo="Finito")
        testo = brief.formatta(brief.componi(config.VAULT_DIR))
        self.assertIn("Nessun filo aperto", testo)


class TestProviderDeepSeek(unittest.TestCase):
    def setUp(self) -> None:
        self._key = config.DEEPSEEK_API_KEY
        self._thinking = config.DEEPSEEK_THINKING
        config.DEEPSEEK_API_KEY = "chiave-finta"

    def tearDown(self) -> None:
        config.DEEPSEEK_API_KEY = self._key
        config.DEEPSEEK_THINKING = self._thinking

    def test_endpoint_e_modello_attesi(self) -> None:
        provider = build_provider("deepseek")
        self.assertEqual(provider.name, "deepseek")
        self.assertEqual(provider.url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(provider.model, "deepseek-flash")

    def test_thinking_spento_per_default(self) -> None:
        # Acceso di default lato DeepSeek a sforzo alto: per turni brevi e'
        # budget speso in ragionamento invece che in risposta.
        config.DEEPSEEK_THINKING = "disabled"
        provider = build_provider("deepseek")
        self.assertEqual(provider.extra_body["thinking"], {"type": "disabled"})
        self.assertNotIn("reasoning_effort", provider.extra_body)

    def test_thinking_acceso_porta_con_se_lo_sforzo(self) -> None:
        config.DEEPSEEK_THINKING = "high"
        provider = build_provider("deepseek")
        self.assertEqual(provider.extra_body["thinking"], {"type": "enabled"})
        self.assertEqual(provider.extra_body["reasoning_effort"], "high")

    def test_senza_chiave_alza_errore(self) -> None:
        config.DEEPSEEK_API_KEY = ""
        with self.assertRaises(ProviderError):
            build_provider("deepseek")


class TestOpenAICompatibile(unittest.TestCase):
    """Il parsing della risposta, senza rete: _post_json viene sostituito."""

    def setUp(self) -> None:
        self._saved = providers._post_json
        self.sent = {}

    def tearDown(self) -> None:
        providers._post_json = self._saved

    def _stub(self, response):
        def fake(url, headers, payload, retries=3):
            self.sent.update({"url": url, "headers": headers, "payload": payload})
            return response
        providers._post_json = fake

    def _provider(self):
        return providers.OpenAICompatibleProvider(
            "test", "https://esempio.test/v1/chat/completions", "m1", "k", "TEST_KEY",
            extra_body={"reasoning_effort": "low"},
        )

    def test_legge_il_contenuto_stringa(self) -> None:
        self._stub({"choices": [{"message": {"content": " risposta "}}]})
        self.assertEqual(self._provider().complete("sys", [{"role": "user", "content": "x"}], 100),
                         "risposta")

    def test_legge_il_contenuto_a_blocchi(self) -> None:
        # Alcuni endpoint restituiscono una lista di blocchi invece di una stringa.
        self._stub({"choices": [{"message": {"content": [
            {"type": "text", "text": "prima "}, {"type": "text", "text": "seconda"}]}}]})
        self.assertEqual(self._provider().complete("sys", [{"role": "user", "content": "x"}], 100),
                         "prima seconda")

    def test_contenuto_vuoto_e_un_errore_esplicito(self) -> None:
        # Un modello che ragiona puo' spendere tutto il budget e non rispondere:
        # deve dirlo, non restituire stringa vuota a valle.
        self._stub({"choices": [{"message": {"content": ""}}]})
        with self.assertRaises(ProviderError) as ctx:
            self._provider().complete("sys", [{"role": "user", "content": "x"}], 100)
        self.assertIn("AGENCY_MAX_TOKENS", str(ctx.exception))

    def test_risposta_senza_choices(self) -> None:
        self._stub({"error": "quota"})
        with self.assertRaises(ProviderError):
            self._provider().complete("sys", [{"role": "user", "content": "x"}], 100)

    def test_system_va_come_primo_messaggio_e_extra_body_passa(self) -> None:
        self._stub({"choices": [{"message": {"content": "ok"}}]})
        self._provider().complete("regole", [{"role": "user", "content": "x"}], 100)
        payload = self.sent["payload"]
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "regole"})
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertEqual(self.sent["headers"]["authorization"], "Bearer k")


class TestProviderAnthropic(unittest.TestCase):
    def test_senza_chiave_alza_errore(self) -> None:
        saved = config.ANTHROPIC_API_KEY
        config.ANTHROPIC_API_KEY = ""
        try:
            with self.assertRaises(ProviderError):
                build_provider("anthropic")
        finally:
            config.ANTHROPIC_API_KEY = saved


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

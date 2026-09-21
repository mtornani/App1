"""Test dell'agenzia: stdlib unittest, nessuna rete, nessuna chiave.

Eseguibili ovunque:  python -m unittest agency.tests.test_agency -v
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

from agency import config, orchestrator, roster, store, tools
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
                       config.INDEX_FILE, config.OUTPUT_DIR)
        config.STATE_DIR = base
        config.MISSIONS_DIR = base / "missions"
        config.RUNS_DIR = base / "runs"
        config.INDEX_FILE = base / "index.json"
        config.OUTPUT_DIR = base / "output"
        config.ensure_dirs()

    def tearDown(self) -> None:
        (config.STATE_DIR, config.MISSIONS_DIR, config.RUNS_DIR,
         config.INDEX_FILE, config.OUTPUT_DIR) = self._saved
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

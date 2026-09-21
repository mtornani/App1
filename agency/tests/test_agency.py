"""Test dell'agenzia: stdlib unittest, nessuna rete, nessuna chiave.

Eseguibili ovunque:  python -m unittest agency.tests.test_agency -v
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

from agency import config, orchestrator, roster, store
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
        self._saved = (config.STATE_DIR, config.MISSIONS_DIR, config.RUNS_DIR, config.INDEX_FILE)
        config.STATE_DIR = base
        config.MISSIONS_DIR = base / "missions"
        config.RUNS_DIR = base / "runs"
        config.INDEX_FILE = base / "index.json"
        config.ensure_dirs()

    def tearDown(self) -> None:
        (config.STATE_DIR, config.MISSIONS_DIR, config.RUNS_DIR, config.INDEX_FILE) = self._saved
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

    def test_anthropic_senza_chiave_alza_errore(self) -> None:
        saved = config.ANTHROPIC_API_KEY
        config.ANTHROPIC_API_KEY = ""
        try:
            with self.assertRaises(ProviderError):
                build_provider("anthropic")
        finally:
            config.ANTHROPIC_API_KEY = saved


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

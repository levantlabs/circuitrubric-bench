"""Tests for the reference runner — no network, using a mock backend."""
from pathlib import Path

from circuitrubric.runner import (
    extract_netlist, run_benchmark, tally_credits, RunConfig,
    run_sweep, format_combined_table,
)
from circuitrubric.task import load_task

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class FakeBackend:
    """Returns a canned fenced response keyed by the user prompt text."""
    backend_id = "fake"

    def __init__(self, by_prompt: dict[str, str]):
        self._by_prompt = by_prompt
        self.calls = 0

    def call(self, model, temperature, max_tokens, system_prompt, user_prompt):
        self.calls += 1
        netlist = self._by_prompt.get(user_prompt, "; no netlist")
        return {
            "raw_text": f"Here you go:\n\n```spice\n{netlist}\n```\n",
            "stop_reason": "stop",
            "latency_ms": 1,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }


def test_extract_netlist_typed_bare_and_missing():
    assert extract_netlist("```spice\nM1 a b 0 0 NMOS\n```")[0] == "M1 a b 0 0 NMOS"
    # bare fence that looks like spice
    assert extract_netlist("```\nM1 a b 0 0 NMOS\n```")[0] == "M1 a b 0 0 NMOS"
    # last fence wins (self-correction)
    two = "```spice\nM1 a b 0 0 NMOS\n```\noops\n```spice\nM2 c d 0 0 NMOS\n```"
    assert extract_netlist(two)[0] == "M2 c d 0 0 NMOS"
    # no fence -> error
    netlist, err = extract_netlist("just prose, no code")
    assert netlist is None and err
    # unfenced netlist with a bare ``spice`` tag line (Qwen-on-OpenRouter style) -> accepted
    unfenced = "spice\nM1 voutn vinp ntail 0 nch W=10u L=1u\nM2 voutp vinn ntail 0 nch W=10u L=1u\n.MODEL nch NMOS"
    net, err = extract_netlist(unfenced)
    assert err is None and net.startswith("M1 voutn") and ".MODEL nch" in net
    # a single prose line that happens to start with a SPICE letter must NOT be accepted
    assert extract_netlist("With a bit of luck this works")[0] is None


def test_run_benchmark_grades_reference_as_full(tmp_path):
    ids = ["001_5t_ota_nmos", "003_nmos_mirror_1to1"]
    # mock returns each fixture's own reference netlist for its `spec` prompt
    by_prompt = {}
    for fid in ids:
        task = next(t for t in load_task(FIXTURES / fid) if t.prompt_id == "spec")
        by_prompt[task.prompt] = (FIXTURES / fid / "reference.cir").read_text()
    backend = FakeBackend(by_prompt)

    config = RunConfig(
        fixtures_dir=FIXTURES, topology_ids=ids, prompt_ids=["spec"], reps=1,
        model="mock", temperature=None, max_tokens=100, system_prompt="be terse",
        output_dir=tmp_path, run_id="t", backend_id="fake",
    )
    summary_path = run_benchmark(config, backend=backend)

    assert backend.calls == 2
    assert summary_path.exists()
    t = tally_credits(summary_path)
    assert t["total"] == 2
    assert t["counts"].get("full") == 2
    assert t["full_rate"] == 1.0
    # raw responses + config persisted
    assert (tmp_path / "t" / "config.json").exists()
    assert len(list((tmp_path / "t" / "raw").glob("*.txt"))) == 2


def test_run_benchmark_resumes_without_recalling(tmp_path):
    fid = "001_5t_ota_nmos"
    task = next(t for t in load_task(FIXTURES / fid) if t.prompt_id == "spec")
    by_prompt = {task.prompt: (FIXTURES / fid / "reference.cir").read_text()}

    def make_cfg():
        return RunConfig(
            fixtures_dir=FIXTURES, topology_ids=[fid], prompt_ids=["spec"], reps=1,
            model="mock", temperature=None, max_tokens=100, system_prompt="be terse",
            output_dir=tmp_path, run_id="t", backend_id="fake",
        )

    b1 = FakeBackend(by_prompt)
    run_benchmark(make_cfg(), backend=b1)
    assert b1.calls == 1
    # second run reuses the saved raw response — no new backend call
    b2 = FakeBackend(by_prompt)
    run_benchmark(make_cfg(), backend=b2)
    assert b2.calls == 0


def test_run_sweep_and_combined_table(tmp_path):
    ids = ["001_5t_ota_nmos", "003_nmos_mirror_1to1"]
    by_prompt = {}
    for fid in ids:
        task = next(t for t in load_task(FIXTURES / fid) if t.prompt_id == "spec")
        by_prompt[task.prompt] = (FIXTURES / fid / "reference.cir").read_text()

    def factory(backend_id, base_url, api_key_env):
        return FakeBackend(by_prompt)

    models = [
        {"backend": "anthropic", "model": "claude-opus-4-8", "label": "opus"},
        {"backend": "ollama", "model": "qwen2.5"},  # label defaults to model
    ]
    results = run_sweep(
        models, fixtures_dir=FIXTURES, topology_ids=ids, prompt_ids=["spec"],
        reps=1, max_tokens=100, system_prompt="x", output_dir=tmp_path,
        timestamp="20260101-000000", backend_factory=factory,
    )
    assert [r["label"] for r in results] == ["opus", "qwen2.5"]
    assert all(r["tally"]["full_rate"] == 1.0 for r in results)
    # per-model result dirs created with slugged run-ids
    assert (tmp_path / "20260101-000000-opus" / "summary.jsonl").exists()
    assert (tmp_path / "20260101-000000-qwen2.5" / "summary.jsonl").exists()

    table = format_combined_table(results)
    assert "| model | FULL% |" in table
    assert "opus" in table and "qwen2.5" in table
    assert "100.0%" in table

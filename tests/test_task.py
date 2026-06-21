from pathlib import Path
from circuitrubric.task import Task, load_task

import pytest
import yaml

FIXTURE = Path(__file__).parent.parent / "fixtures" / "001_5t_ota_nmos"


def test_load_returns_list_of_tasks():
    tasks = load_task(FIXTURE)
    assert isinstance(tasks, list)
    assert len(tasks) == 3
    assert all(isinstance(t, Task) for t in tasks)


def test_task_identifiers():
    tasks = load_task(FIXTURE)
    ids = sorted(t.id for t in tasks)
    assert ids == [
        "001_5t_ota_nmos.short",
        "001_5t_ota_nmos.spec",
        "001_5t_ota_nmos.verbose",
    ]
    topology_ids = {t.topology_id for t in tasks}
    assert topology_ids == {"001_5t_ota_nmos"}
    prompt_ids = sorted(t.prompt_id for t in tasks)
    assert prompt_ids == ["short", "spec", "verbose"]


def test_short_prompt_text():
    tasks = load_task(FIXTURE)
    short = next(t for t in tasks if t.prompt_id == "short")
    assert short.prompt == "Design a 5T OTA with NMOS inputs."


def test_verbose_prompt_text():
    tasks = load_task(FIXTURE)
    verbose = next(t for t in tasks if t.prompt_id == "verbose")
    assert verbose.prompt.startswith("Design a single-stage differential amplifier")


def test_tasks_share_reference_and_ratio_groups():
    tasks = load_task(FIXTURE)
    refs = {tuple(t.references) for t in tasks}
    rgs = {tuple((g.devices[0], tuple(g.ratio_W)) for g in t.ratio_groups) for t in tasks}
    assert len(refs) == 1
    assert len(rgs) == 1


def test_meta_loaded_per_task():
    tasks = load_task(FIXTURE)
    for t in tasks:
        assert t.meta.id == "001_5t_ota_nmos"
        assert t.meta.family == "5T_OTA"
        assert t.meta.variant == "nmos_input"


def test_load_rejects_missing_prompts(tmp_path):
    src = FIXTURE
    dst = tmp_path / "001_no_prompts"
    dst.mkdir()
    for f in ["ratio_groups.yaml", "meta.yaml", "reference.cir"]:
        (dst / f).write_text((src / f).read_text())
    with pytest.raises(FileNotFoundError):
        load_task(dst)


def test_load_rejects_malformed_meta(tmp_path):
    src = FIXTURE
    dst = tmp_path / "001_bad_meta"
    dst.mkdir()
    for f in ["ratio_groups.yaml", "reference.cir"]:
        (dst / f).write_text((src / f).read_text())
    (dst / "prompts.yaml").write_text("prompts:\n  - id: test\n    text: test\n")
    (dst / "meta.yaml").write_text("id: only_id_present\n")
    with pytest.raises(Exception):
        load_task(dst)


def test_load_rejects_missing_reference(tmp_path):
    src = FIXTURE
    dst = tmp_path / "001_no_ref"
    dst.mkdir()
    for f in ["ratio_groups.yaml", "meta.yaml"]:
        (dst / f).write_text((src / f).read_text())
    (dst / "prompts.yaml").write_text("prompts:\n  - id: test\n    text: test\n")
    with pytest.raises(FileNotFoundError):
        load_task(dst)


def test_ratio_group_devices_match_ratio_lengths(tmp_path):
    src = FIXTURE
    dst = tmp_path / "001_mismatch"
    dst.mkdir()
    for f in ["meta.yaml", "reference.cir"]:
        (dst / f).write_text((src / f).read_text())
    (dst / "prompts.yaml").write_text("prompts:\n  - id: test\n    text: test\n")
    (dst / "ratio_groups.yaml").write_text(
        "groups:\n  - devices: [M1, M2, M3]\n    ratio_W: [1, 1]\n    ratio_L: [1, 1]\n"
    )
    with pytest.raises(Exception):
        load_task(dst)


def test_load_multiple_reference_variants(tmp_path):
    """When a topology has reference.cir AND reference_alt_1.cir, both are
    returned in task.references for every prompt variant."""
    src = FIXTURE
    dst = tmp_path / "001_multi_ref"
    dst.mkdir()
    for f in ["ratio_groups.yaml", "meta.yaml", "reference.cir"]:
        (dst / f).write_text((src / f).read_text())
    (dst / "prompts.yaml").write_text("prompts:\n  - id: test\n    text: test\n")
    (dst / "reference_alt_1.cir").write_text((src / "reference.cir").read_text())
    tasks = load_task(dst)
    for t in tasks:
        assert len(t.references) == 2
        assert t.references[0].name == "reference.cir"
        assert t.references[1].name == "reference_alt_1.cir"


def test_list_tasks_flattens_across_topologies(tmp_path):
    """list_tasks loads N topology dirs, each with M prompts, returning M*N tasks
    sorted by topology then by prompt order."""
    for slug in ["003_alpha", "001_beta", "002_gamma"]:
        d = tmp_path / slug
        d.mkdir()
        for f in ["ratio_groups.yaml", "meta.yaml", "reference.cir"]:
            (d / f).write_text((FIXTURE / f).read_text())
        (d / "prompts.yaml").write_text("prompts:\n  - id: short\n    text: short\n  - id: verbose\n    text: verbose\n")
        meta = yaml.safe_load((FIXTURE / "meta.yaml").read_text())
        meta["id"] = slug
        (d / "meta.yaml").write_text(yaml.safe_dump(meta))
    from circuitrubric.task import list_tasks
    tasks = list_tasks(tmp_path)
    # 3 topologies × 2 prompts each = 6 tasks
    assert len(tasks) == 6
    topology_ids = [t.topology_id for t in tasks]
    # sorted by topology dir first
    assert topology_ids == ["001_beta", "001_beta", "002_gamma", "002_gamma", "003_alpha", "003_alpha"]


def test_cli_show_lists_all_prompt_variants(capsys):
    from circuitrubric.cli import main
    rc = main(["show", "--task", str(FIXTURE)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "001_5t_ota_nmos" in captured.out
    assert "short" in captured.out
    assert "verbose" in captured.out

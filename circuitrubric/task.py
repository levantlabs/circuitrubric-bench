"""Task data model: load topology task variants from a directory.

Each directory under `fixtures/` or `tasks/` is one
topology with N prompt variants. `load_task` returns one Task instance per
prompt variant; they all share the same references and ratio_groups.
"""

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, model_validator


class RatioGroup(BaseModel):
    devices: List[str]
    ratio_W: Optional[List[float]] = None
    ratio_L: Optional[List[float]] = None
    ratio_M: Optional[List[float]] = None
    ratio_value: Optional[List[float]] = None

    @model_validator(mode="after")
    def check_lengths_and_consistency(self):
        n = len(self.devices)
        for field_name in ("ratio_W", "ratio_L", "ratio_M", "ratio_value"):
            value = getattr(self, field_name)
            if value is not None and len(value) != n:
                raise ValueError(
                    f"{field_name} ({len(value)}) must have one entry per device ({n})"
                )
        has_mos = self.ratio_W is not None or self.ratio_L is not None
        has_pas = self.ratio_value is not None
        if has_mos and has_pas:
            raise ValueError(
                "ratio group cannot mix MOSFET ratios (ratio_W/ratio_L) with "
                "passive ratio (ratio_value)"
            )
        if not has_mos and not has_pas:
            raise ValueError(
                "ratio group must declare ratio_W/ratio_L (MOSFETs) or "
                "ratio_value (passives)"
            )
        if has_mos and (self.ratio_W is None or self.ratio_L is None):
            raise ValueError(
                "MOSFET ratio group requires both ratio_W and ratio_L"
            )
        if has_pas and self.ratio_M is not None:
            raise ValueError(
                "ratio_M is for MOSFET groups; cannot be set on a passive group"
            )
        return self


class TaskMeta(BaseModel):
    id: str
    category: str
    family: str
    variant: str
    source: str
    attribution: Optional[str] = None


class Task(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str               # composite "<topology_id>.<prompt_id>"
    topology_id: str
    prompt_id: str
    prompt: str
    references: List[Path]
    ratio_groups: List[RatioGroup]
    meta: TaskMeta


def load_task(task_dir: Path) -> List[Task]:
    """Load all Task variants from a single topology directory."""
    task_dir = Path(task_dir)
    prompts_path = task_dir / "prompts.yaml"
    if not prompts_path.exists():
        raise FileNotFoundError(f"No prompts.yaml in {task_dir}")
    references = sorted(task_dir.glob("reference*.cir"))
    if not references:
        raise FileNotFoundError(f"No reference*.cir in {task_dir}")
    with prompts_path.open() as f:
        prompts_data = yaml.safe_load(f) or {}
    prompt_entries = prompts_data.get("prompts", [])
    if not prompt_entries:
        raise ValueError(f"prompts.yaml in {task_dir} has no 'prompts' entries")

    with (task_dir / "ratio_groups.yaml").open() as f:
        groups_data = yaml.safe_load(f) or {"groups": []}
    ratio_groups = [RatioGroup(**g) for g in groups_data.get("groups", [])]

    with (task_dir / "meta.yaml").open() as f:
        meta_data = yaml.safe_load(f)
    meta = TaskMeta(**meta_data)

    tasks: List[Task] = []
    for entry in prompt_entries:
        prompt_id = entry["id"]
        tasks.append(Task(
            id=f"{meta.id}.{prompt_id}",
            topology_id=meta.id,
            prompt_id=prompt_id,
            prompt=entry["text"],
            references=references,
            ratio_groups=ratio_groups,
            meta=meta,
        ))
    return tasks


def list_tasks(root: Path) -> List[Task]:
    """Load all task variants under `root`. Flattens across topology dirs."""
    root = Path(root)
    task_dirs = sorted(
        d for d in root.iterdir()
        if d.is_dir() and d.name[:3].isdigit() and "_" in d.name
    )
    tasks: List[Task] = []
    for d in task_dirs:
        tasks.extend(load_task(d))
    return tasks

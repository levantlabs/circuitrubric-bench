"""CircuitRubric — a structural benchmark for LLM-generated analog netlists.

Public API:
    grade(submission_text, task) -> GradeResult   # grade a netlist against a fixture
    load_task(path) -> list[Task]                 # load a fixture's task variants
    Credit                                        # the 6-level credit ladder
    parse_netlist / load_netlist                  # netlist parsing helpers

Example:
    from circuitrubric import grade, load_task
    task = load_task("fixtures/001_5t_ota_nmos")[0]
    result = grade(open("my_netlist.cir").read(), task)
    print(result.credit)        # Credit.FULL / PARTIAL / ... / NONE
"""

from circuitrubric.grader import grade, GradeResult, Credit
from circuitrubric.task import Task, RatioGroup, load_task
from circuitrubric.netlist import Netlist, parse_netlist, load_netlist

__all__ = [
    "grade", "GradeResult", "Credit",
    "Task", "RatioGroup", "load_task",
    "Netlist", "parse_netlist", "load_netlist",
]

__version__ = "0.1.0"

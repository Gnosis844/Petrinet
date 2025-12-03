# task4_deadlock_ilp.py

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import pulp


@dataclass
class Transition:
    """
    Simple representation of a Petri net transition.
    - name: transition identifier
    - pre:  list of input places (preset)
    - post: list of output places (postset)
    """
    name: str
    pre: List[str]
    post: List[str]

def find_deadlock_with_ilp(
    places: List[str],
    transitions: List[Transition],
    reachable_markings: List[Dict[str, int]],
) -> Tuple[bool, Optional[Dict[str, int]]]:
    """
    Find one reachable deadlock marking using ILP.
    """

    # -------------------------------------------------
    # 0. Quick check: if there exists a transition with
    #    empty preset, then it is always enabled in any
    #    marking. Therefore, there is NO dead marking.
    # -------------------------------------------------
    if any(len(t.pre) == 0 for t in transitions):
        return False, None

    # 1. Create ILP problem (feasibility)
    problem = pulp.LpProblem("Deadlock_Detection", pulp.LpStatusOptimal)

    # 2. Binary vars M_p for each place p
    M_vars = {
        p: pulp.LpVariable(f"M_{p}", lowBound=0, upBound=1, cat="Binary")
        for p in places
    }

    # 3. Selector vars y_i for reachable markings
    y_vars = [
        pulp.LpVariable(f"y_{i}", lowBound=0, upBound=1, cat="Binary")
        for i in range(len(reachable_markings))
    ]

    # Exactly one reachable marking is selected
    problem += pulp.lpSum(y_vars) == 1, "Select_exactly_one_reachable_marking"

    # 4. Link M to reachable markings via y_i
    for p in places:
        problem += (
            M_vars[p]
            == pulp.lpSum(
                y_vars[i] * reachable_markings[i][p]
                for i in range(len(reachable_markings))
            )
        ), f"Link_M_{p}_to_reachables"

    # 5. Dead marking constraints:
    #    For each transition t:
    #      sum(M[p] for p in pre(t)) <= |pre(t)| - 1  (t disabled)
    for t in transitions:
        # no need for empty-preset branch anymore (handled at top)
        problem += (
            pulp.lpSum(M_vars[p] for p in t.pre) <= len(t.pre) - 1
        ), f"Disable_transition_{t.name}"

    # 6. Dummy objective
    problem += 0, "Dummy_Objective"

    # 7. Solve
    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[status] != "Optimal":
        return False, None

    # 8. Extract marking
    deadlock_marking = {p: int(round(M_vars[p].value())) for p in places}
    return True, deadlock_marking
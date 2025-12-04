"""
Task 4: Deadlock detection using ILP over reachable markings.

- Input:
    * places: list of place IDs (strings)
    * transitions: list of DeadlockTransition (name, pre, post)
    * reachable_markings: list of markings, each marking is a dict:
          { place_id: 0 or 1 }
      (these markings are assumed to be reachable from Task 2/Task 3)

- Output:
    * (found, marking)
      - found: True if exists a reachable deadlock marking, otherwise False
      - marking: dict {place_id: 0/1} if found=True, otherwise None

Idea:
- Use selector variable y_i ∈ {0,1} to select exactly one marking in reachable_markings.
- Link M_p = Σ_i y_i * reachable_markings[i][p].
- Add constraint "deadlock": for every transition t,
      Σ_{p ∈ pre(t)} M_p ≤ |pre(t)| - 1
  ⇒ no transition is enabled.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import pulp


@dataclass
class DeadlockTransition:
    """
    Simple representation of a Petri net transition for Task 4.

    Attributes
    ----------
    name : str
        Transition identifier (for logging / debugging).
    pre : List[str]
        List of input places (preset): places that must have tokens
        for the transition to be enabled.
    post : List[str]
        List of output places (postset).
        (Not used in ILP deadlock check, but kept for completeness.)
    """
    name: str
    pre: List[str]
    post: List[str]


def find_deadlock_with_ilp(
    places: List[str],
    transitions: List[DeadlockTransition],
    reachable_markings: List[Dict[str, int]],
) -> Tuple[bool, Optional[Dict[str, int]]]:
    """
    Find one reachable deadlock marking using ILP.

    Parameters
    ----------
    places : List[str]
        List of place IDs in the net.
    transitions : List[DeadlockTransition]
        Transitions with preset (pre) and postset (post).
    reachable_markings : List[Dict[str, int]]
        List of reachable markings. Each marking is a dict {place_id: 0 or 1}.

    Returns
    -------
    found : bool
        True if a reachable deadlock marking exists, False otherwise.
    marking : Optional[Dict[str, int]]
        One reachable deadlock marking (0/1 per place) if found=True, else None.
    """

    # -------------------------------------------------
    # 0. Quick check: if there exists a transition with
    #    empty preset, then it is always enabled in any
    #    marking. Therefore, there is NO dead marking.
    # -------------------------------------------------
    if any(len(t.pre) == 0 for t in transitions):
        return False, None

    # -------------------------------------------------
    # 1. Create ILP problem (feasibility)
    #    We don't optimize anything; just look for a feasible solution.
    # -------------------------------------------------
    problem = pulp.LpProblem("Deadlock_Detection", pulp.LpMinimize)

    # -------------------------------------------------
    # 2. Binary vars M_p for each place p (0/1 tokens)
    # -------------------------------------------------
    M_vars: Dict[str, pulp.LpVariable] = {
        p: pulp.LpVariable(f"M_{p}", lowBound=0, upBound=1, cat="Binary")
        for p in places
    }

    # -------------------------------------------------
    # 3. Selector vars y_i for each reachable marking i
    #    y_i = 1 ⇔ we choose marking i.
    # -------------------------------------------------
    y_vars: List[pulp.LpVariable] = [
        pulp.LpVariable(f"y_{i}", lowBound=0, upBound=1, cat="Binary")
        for i in range(len(reachable_markings))
    ]

    # Exactly one reachable marking is selected
    problem += pulp.lpSum(y_vars) == 1, "Select_exactly_one_reachable_marking"

    # -------------------------------------------------
    # 4. Link M to reachable markings via y_i:
    #
    #    For each place p:
    #        M_p = Σ_i y_i * reachable_markings[i][p]
    #
    #    This enforces that (M_p)_p is exactly one of the
    #    reachable markings in reachable_markings.
    # -------------------------------------------------
    for p in places:
        problem += (
            M_vars[p]
            == pulp.lpSum(
                y_vars[i] * reachable_markings[i][p]
                for i in range(len(reachable_markings))
            )
        ), f"Link_M_{p}_to_reachables"

    # -------------------------------------------------
    # 5. Dead marking constraints:
    #
    #    A marking M is dead if no transition is enabled.
    #    For a transition t with preset pre(t):
    #       t enabled ⇔ ∀ p ∈ pre(t): M_p = 1
    #
    #    To force "t is disabled", we require:
    #       Σ_{p ∈ pre(t)} M_p ≤ |pre(t)| - 1
    #
    #    We add this for every transition t.
    # -------------------------------------------------
    for t in transitions:
        if not t.pre:
            # theoretically shouldn't happen here because of the early return
            # but we keep the guard for safety
            continue

        problem += (
            pulp.lpSum(M_vars[p] for p in t.pre) <= len(t.pre) - 1
        ), f"Disable_transition_{t.name}"

    # -------------------------------------------------
    # 6. Dummy objective (we only need a feasible solution)
    # -------------------------------------------------
    problem += 0, "Dummy_Objective"

    # -------------------------------------------------
    # 7. Solve
    # -------------------------------------------------
    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[status] != "Optimal":
        # No feasible marking satisfying "reachable + deadlock"
        return False, None

    # -------------------------------------------------
    # 8. Extract marking
    # -------------------------------------------------
    deadlock_marking: Dict[str, int] = {
        p: int(round(M_vars[p].value() or 0)) for p in places
    }
    return True, deadlock_marking


__all__ = ["DeadlockTransition", "find_deadlock_with_ilp"]

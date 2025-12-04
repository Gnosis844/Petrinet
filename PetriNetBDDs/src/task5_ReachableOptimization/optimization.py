"""
Task 5: Optimization over reachable markings.

Goal:
    Maximize c^T M  subject to  M ∈ Reach(M0),
where:
    - M is a 0/1 marking (1-safe net),
    - Reach(M0) is determined by Task 3 (BDD symbolic reachability),
    - c is a user-defined weight vector over places.

Approach:
    - Extend PNModel to compute the incidence matrix A = Post - Pre.
    - Use an ILP with state equation:
          M = M0 + A * sigma
      where sigma[t] is the (integer) firing count of transition t.
    - After solving the ILP, verify the resulting marking M against
      the BDD reachable set from Task 3.
    - If the ILP optimum is NOT reachable, add a no-good cut and solve again
      (advanced part), until a reachable optimum is found or no solution exists.
"""

from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pulp
from dd.autoref import BDD

from task1_PnmlParsing.pnml_parser import PNModel          # Task 1
from task3_BddBasedReachability.symbolic import SymbolicAnalyzer    # Task 3


# ====================================================================
# PART 1: Extend PNModel with incidence matrix A = Post - Pre
# ====================================================================

def _build_incidence_matrix(self: PNModel) -> np.ndarray:
    """
    Compute and return the incidence matrix A = Post - Pre.

    Rows correspond to places (sorted by place ID).
    Columns correspond to transitions (sorted by transition ID).

    For a place p and transition t:
        A[p, t] =  1  if there is an arc t -> p  (postset)
                = -1  if there is an arc p -> t  (preset)
                =  0  otherwise
    """
    sorted_places = sorted(self.places.keys())
    sorted_transitions = sorted(self.transitions.keys())
    n_places = len(sorted_places)
    n_trans = len(sorted_transitions)

    A = np.zeros((n_places, n_trans), dtype=int)
    p_idx = {p: i for i, p in enumerate(sorted_places)}

    for p_id in sorted_places:
        i = p_idx[p_id]
        for j, t_id in enumerate(sorted_transitions):
            # By construction in PNModel:
            #   place.inputs  = transitions -> place (postset)
            #   place.outputs = place -> transitions (preset)
            post_val = 1 if t_id in self.places[p_id].inputs else 0
            pre_val = 1 if t_id in self.places[p_id].outputs else 0
            A[i, j] = post_val - pre_val

    return A


# Add as a read-only property on PNModel
PNModel.incidence_matrix = property(_build_incidence_matrix)


# ====================================================================
# PART 2: Integrate BDD reachability (Task 3) and ILP core
# ====================================================================

def get_bdd_reach_data(model: PNModel) -> Tuple[BDD, Any, Dict[str, str]]:
    """
    Run the SymbolicAnalyzer (Task 3) to obtain:

    - bdd_instance: the BDD manager
    - reachable_bdd: BDD node representing Reach(M0)
    - place_vars: mapping place_id -> BDD variable name
    """
    print("\n[Task 5] Running SymbolicAnalyzer from Task 3...")
    analyzer = SymbolicAnalyzer(model)
    results = analyzer.analyze()

    bdd_instance: BDD = analyzer.bdd
    reachable_bdd = analyzer.reachable_bdd
    place_vars = analyzer.place_vars

    print(
        f"[Task 5] Symbolic reachability done. "
        f"BDD nodes: {results['bdd_node_count']}, "
        f"reachable markings: {results['num_markings']}"
    )
    # We do not propagate the timing information here; Task 5 focuses
    # on the ILP optimization itself.

    return bdd_instance, reachable_bdd, place_vars


def is_reachable_bdd(
    marking_dict: Dict[str, int],
    bdd_reach: Any,
    place_vars: Dict[str, str],
    bdd_instance: BDD,
) -> bool:
    """
    Check if a given marking dictionary is contained in the BDD reachable set.

    Parameters
    ----------
    marking_dict : Dict[str, int]
        Mapping place_id -> 0 or 1.
    bdd_reach : BDD node
        BDD representing Reach(M0) from Task 3.
    place_vars : Dict[str, str]
        Mapping place_id -> BDD variable name.
    bdd_instance : BDD
        BDD manager (dd.autoref.BDD instance).

    Returns
    -------
    bool
        True if the marking is in Reach(M0), False otherwise.
    """
    fs_marking = frozenset(p for p, val in marking_dict.items() if val == 1)
    marking_bdd = bdd_instance.true

    for place_id, var_name in place_vars.items():
        var = bdd_instance.var(var_name)
        if place_id in fs_marking:
            marking_bdd = marking_bdd & var
        else:
            marking_bdd = marking_bdd & ~var

    return (marking_bdd & bdd_reach) != bdd_instance.false


def optimize_reachable(
    model: PNModel,
    c: Dict[str, int],
    timeout: int = 60,
    max_cuts: int = 50,
) -> Tuple[Optional[Dict[str, int]], str]:
    """
    Task 5 (with advanced part): Solve

        max  c^T M
        s.t. M ∈ Reach(M0)

    using:
      - state equation M = M0 + A * sigma
      - BDD-based reachability check from Task 3
      - iterative no-good cuts to eliminate ILP-optimal markings
        that are not actually reachable.

    Parameters
    ----------
    model : PNModel
        Petri net model from Task 1.
    c : Dict[str, int]
        Objective weight vector: place_id -> weight c_p.
    timeout : int
        Time limit in seconds for EACH ILP solve call.
    max_cuts : int
        Maximum number of no-good cuts to add before giving up.

    Returns
    -------
    (optimal_M, log_messages)
        - optimal_M: dict {place_id: 0/1} for an optimal reachable marking,
                     or None if no feasible reachable marking was found.
        - log_messages: textual log describing solver status, cuts, and checks.
    """
    # 1. Obtain BDD reachable set from Task 3
    bdd_instance, bdd_reach, place_vars = get_bdd_reach_data(model)

    # 2. Setup ILP (structure is created once; we will re-solve with extra cuts)
    places: List[str] = sorted(model.places.keys())
    transitions: List[str] = sorted(model.transitions.keys())
    A: np.ndarray = model.incidence_matrix

    prob = pulp.LpProblem("Petri_Optimization", pulp.LpMaximize)

    # Binary marking variables M[p] ∈ {0, 1}
    M_vars = pulp.LpVariable.dicts("M", places, lowBound=0, upBound=1, cat=pulp.LpBinary)
    # Non-negative integer firing counts sigma[t] ≥ 0
    sigma_vars = pulp.LpVariable.dicts("sigma", transitions, lowBound=0, cat=pulp.LpInteger)

    # Objective: max sum_p c_p * M_p
    prob += pulp.lpSum(c.get(p, 0) * M_vars[p] for p in places), "Objective_cT_M"

    # State Equation:  M = M0 + A * sigma
    for i, p in enumerate(places):
        M0_p = 1 if model.places[p].marked else 0
        prob += (
            M_vars[p]
            == M0_p + pulp.lpSum(A[i, j] * sigma_vars[t] for j, t in enumerate(transitions))
        ), f"State_Eq_{p}"

    # 3. Iteratively solve the ILP and apply BDD check + no-good cuts
    log_messages = ""
    cut_count = 0
    iteration = 0

    while True:
        iteration += 1
        log_messages += f"\n[Task 5] ILP solve iteration #{iteration} (cuts so far: {cut_count})\n"

        status = prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=timeout))
        status_str = pulp.LpStatus.get(status, "Unknown")
        log_messages += f"  Solver status: {status_str}\n"

        # If ILP is infeasible or not optimal, we cannot proceed further
        if status_str != "Optimal":
            log_messages += (
                "  No optimal solution found at this iteration. "
                "Stopping optimization.\n"
            )
            return None, log_messages

        # Extract current optimal marking from ILP
        optimal_M: Dict[str, int] = {
            p: int(round(M_vars[p].value() or 0)) for p in places
        }
        log_messages += f"  ILP candidate marking: {optimal_M}\n"

        # Check reachability via BDD
        if is_reachable_bdd(optimal_M, bdd_reach, place_vars, bdd_instance):
            log_messages += (
                "  Candidate marking is consistent with BDD reachable set.\n"
                "  -> Accepted as optimal reachable marking.\n"
            )
            return optimal_M, log_messages

        # If not reachable, add a no-good cut to exclude this marking and try again
        log_messages += (
            "  Candidate marking does NOT satisfy BDD reachability.\n"
            "  Adding a no-good cut to exclude this marking and re-solving.\n"
        )

        ones = [p for p, v in optimal_M.items() if v == 1]
        zeros = [p for p, v in optimal_M.items() if v == 0]

        # No-good cut:
        #   Σ_{p ∈ ones} (1 - M_p) + Σ_{p ∈ zeros} M_p ≥ 1
        # This forces the next solution to differ in at least one M_p.
        prob += (
            pulp.lpSum(1 - M_vars[p] for p in ones)
            + pulp.lpSum(M_vars[p] for p in zeros)
            >= 1
        ), f"NoGoodCut_{cut_count}"

        cut_count += 1
        if cut_count >= max_cuts:
            log_messages += (
                f"  Reached maximum number of cuts ({max_cuts}). "
                "Stopping optimization without a reachable solution.\n"
            )
            return None, log_messages


__all__ = [
    "get_bdd_reach_data",
    "is_reachable_bdd",
    "optimize_reachable",
]

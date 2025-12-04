"""
Task 2: Explicit reachability analysis for 1-safe Petri nets.
- Uses PNModel from Task 1 (pnml_parser.py).
- Enumerates all reachable markings using BFS (explicit state space).
- Optionally detects deadlock markings (no enabled transitions).
- Provides run_explicit_analysis(...) that later can be called from main.py
  or from experiment scripts.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Dict, List, Set, Tuple, FrozenSet

from task1_PnmlParsing.pnml_parser import PNModel


Marking = FrozenSet[str]  # a marking is a frozenset of place IDs


# ------------------------------------------------------------
#  Enabled / Firing
# ------------------------------------------------------------

def is_enabled(model: PNModel, marking: Marking, tid: str) -> bool:
    """
    Check if transition 'tid' is enabled in the given marking.

    A transition t is enabled iff all its input places contain a token.
    Since the net is 1-safe, we represent a marking as a frozenset of
    place IDs that currently have a token.
    """
    t = model.transitions[tid]
    # t.inputs is a list of place IDs required by this transition
    return all(p in marking for p in t.inputs)


def fire(model: PNModel, marking: Marking, tid: str) -> Marking:
    """
    Fire transition 'tid' from the given marking.

    - Removes tokens from all input places of 'tid'.
    - Adds tokens to all output places of 'tid'.
    - Returns the new marking as a frozenset of place IDs.
    """
    t = model.transitions[tid]
    newM = set(marking)

    # Remove tokens from preset
    for p in t.inputs:
        if p in newM:
            newM.remove(p)

    # Add tokens to postset
    for p in t.outputs:
        newM.add(p)

    return frozenset(newM)


# ------------------------------------------------------------
#  Explicit reachability (BFS)
# ------------------------------------------------------------

def initial_marking(model: PNModel) -> Marking:
    """
    Build the initial marking M0 from the PNModel.

    We assume a 1-safe net where each place has either 0 or 1 token initially,
    encoded by Place.marked in PNModel.
    """
    return frozenset(p_id for p_id, p in model.places.items() if p.marked)


def explicit_reachability(model: PNModel) -> Tuple[Set[Marking], List[Tuple[Marking, str, Marking]]]:
    """
    Perform explicit BFS reachability analysis.

    Returns
    -------
    visited : Set[Marking]
        The set of all reachable markings from the initial marking M0.
    edges : List[(M, tid, M2)]
        The list of transitions fired along the reachability graph:
        each element is (source_marking, transition_id, successor_marking).
    """
    M0 = initial_marking(model)

    visited: Set[Marking] = {M0}
    queue: deque[Marking] = deque([M0])
    edges: List[Tuple[Marking, str, Marking]] = []

    while queue:
        M = queue.popleft()

        # Try firing all transitions from marking M
        for tid in model.transitions:
            if is_enabled(model, M, tid):
                M2 = fire(model, M, tid)
                edges.append((M, tid, M2))

                if M2 not in visited:
                    visited.add(M2)
                    queue.append(M2)

    return visited, edges


# ------------------------------------------------------------
#  Deadlock detection (optional helper)
# ------------------------------------------------------------

def find_deadlocks(model: PNModel, states: Set[Marking]) -> List[Marking]:
    """
    Find all deadlock markings among 'states'.

    A deadlock marking M is one where no transition is enabled.
    This is mainly a helper to cross-check with Task 4 (ILP-based deadlock).
    """
    deadlocks: List[Marking] = []
    for M in states:
        if not any(is_enabled(model, M, tid) for tid in model.transitions):
            deadlocks.append(M)
    return deadlocks


# ------------------------------------------------------------
#  Experiment / analysis helper for Task 2
# ------------------------------------------------------------

def run_explicit_analysis(model: PNModel, model_name: str, print_details: bool = True) -> Dict:
    """
    Run explicit reachability + (optional) deadlock detection on a given model.

    Parameters
    ----------
    model : PNModel
        The Petri net model loaded from PNML.
    model_name : str
        Name of the model (usually the PNML filename).
    print_details : bool
        If True, print reachable graph and deadlocks for small models.

    Returns
    -------
    stats : Dict
        A dictionary containing:
          - 'model_name'
          - 'num_places'
          - 'num_transitions'
          - 'num_arcs'
          - 'num_states'
          - 'num_deadlocks'
          - 'time_seconds'
    """
    num_places = len(model.places)
    num_transitions = len(model.transitions)
    num_arcs = len(model.arcs)

    start = time.time()
    states, edges = explicit_reachability(model)
    duration = time.time() - start

    deadlocks = find_deadlocks(model, states)

    if print_details:
        print("\n===== EXPLICIT REACHABILITY:", model_name, "=====")
        print(f"Places      : {num_places}")
        print(f"Transitions : {num_transitions}")
        print(f"Arcs        : {num_arcs}")
        print(f"Reachable   : {len(states)} markings")
        print(f"Deadlocks   : {len(deadlocks)} markings")
        print(f"Time        : {duration:.6f} seconds")

        # Only print full graph / markings if the state space is small
        if len(states) <= 50:
            print("\n-- Reachability edges --")
            for M, t, M2 in edges:
                print(f"{sorted(M)} --{t}--> {sorted(M2)}")

            print("\n-- Deadlock markings --")
            if deadlocks:
                for M in deadlocks:
                    print("Deadlock:", sorted(M))
            else:
                print("None.")
        else:
            print("\n(State space too large, edges/markings not printed.)")

    stats: Dict = {
        "model_name": model_name,
        "num_places": num_places,
        "num_transitions": num_transitions,
        "num_arcs": num_arcs,
        "num_states": len(states),
        "num_deadlocks": len(deadlocks),
        "time_seconds": duration,
    }
    return stats


__all__ = [
    "Marking",
    "is_enabled",
    "fire",
    "initial_marking",
    "explicit_reachability",
    "find_deadlocks",
    "run_explicit_analysis",
]

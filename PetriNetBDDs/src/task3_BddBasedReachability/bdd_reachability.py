# symbolic.py
"""
Task 3: Symbolic Reachability Analysis using Binary Decision Diagrams (BDD)

Integrates with Task 1 (pnml_parser.py) and Task 2 (explicit_reachability.py).

This module provides symbolic state space exploration using BDDs,
which is more efficient for large Petri nets (in terms of memory)
for many models.
"""

import time
from typing import Dict, Set, FrozenSet, Optional

from dd.autoref import BDD
from pnml_parser import PNModel


Marking = FrozenSet[str]


class SymbolicAnalyzer:
    """
    Symbolic reachability analysis using Binary Decision Diagrams.

    This class takes a PNModel from Task 1 and computes reachable markings
    symbolically using BDDs, providing a compact representation of the state space.
    """

    def __init__(self, model: PNModel) -> None:
        """
        Initialize symbolic analyzer with a Petri net model.

        Args:
            model: PNModel object from Task 1 (pnml_parser.py)
        """
        self.model: PNModel = model
        self.bdd: BDD = BDD()
        self.place_vars: Dict[str, str] = {}  # Maps place_id -> BDD variable name
        self.reachable_bdd = None
        self.num_reachable: int = 0

    # ------------------------------------------------------------
    #  Variable encoding
    # ------------------------------------------------------------

    def initialize_bdd_variables(self) -> None:
        """
        Create BDD variables for each place in the Petri net.

        For 1-safe nets, each place needs one boolean variable.
        """
        # Sort places for consistent variable ordering
        sorted_places = sorted(self.model.places.keys())

        for place_id in sorted_places:
            var_name = f"{place_id}_0"
            self.bdd.add_var(var_name)
            self.place_vars[place_id] = var_name

        print(f"Initialized {len(self.place_vars)} BDD variables")

    # ------------------------------------------------------------
    #  Marking <-> BDD conversions
    # ------------------------------------------------------------

    def marking_to_bdd(self, marking: Marking) -> BDD:
        """
        Convert a marking (set of place IDs) to a BDD node.

        Args:
            marking: frozenset or set of place IDs that have tokens

        Returns:
            BDD node representing this marking
        """
        # Create conjunction of literals
        expr = self.bdd.true

        for place_id in self.model.places:
            var_name = self.place_vars[place_id]

            if place_id in marking:
                # Place has token
                expr = expr & self.bdd.var(var_name)
            else:
                # Place has no token
                expr = expr & ~self.bdd.var(var_name)

        return expr

    def bdd_to_markings(self, bdd_node) -> Set[Marking]:
        """
        Extract all markings represented by a BDD node.

        Args:
            bdd_node: BDD node

        Returns:
            Set of markings (each marking is a frozenset of place IDs)
        """
        if bdd_node == self.bdd.false:
            return set()

        markings: Set[Marking] = set()

        # Consume iterator immediately to avoid surprises
        assignments = list(self.bdd.pick_iter(bdd_node))

        for assignment in assignments:
            marking = set()
            for place_id, var_name in self.place_vars.items():
                if assignment.get(var_name, False):
                    marking.add(place_id)
            markings.add(frozenset(marking))

        return markings

    # ------------------------------------------------------------
    #  Symbolic enabling & image
    # ------------------------------------------------------------

    def is_enabled_bdd(self, marking_set, tid: str):
        """
        Symbolically restrict to markings that enable transition 'tid'.

        Args:
            marking_set: BDD representing a set of markings
            tid: Transition ID

        Returns:
            BDD representing markings where transition is enabled
        """
        t = self.model.transitions[tid]

        # Build enabling condition: all input places must have tokens
        enable = self.bdd.true
        for place_id in t.inputs:
            var_name = self.place_vars[place_id]
            enable = enable & self.bdd.var(var_name)

        # Return markings that satisfy the enabling condition
        return marking_set & enable

    def compute_image(self, marking_set, tid: str):
        """
        Compute the symbolic image: all markings reachable by firing a transition.

        Args:
            marking_set: BDD representing a set of markings
            tid: Transition ID to fire

        Returns:
            BDD representing successor markings
        """
        t = self.model.transitions[tid]

        # Get markings where transition is enabled
        enabled_states = self.is_enabled_bdd(marking_set, tid)

        if enabled_states == self.bdd.false:
            return self.bdd.false

        # NOTE: This implementation is "semi-symbolic":
        # we enumerate satisfying assignments of the BDD, then fire explicitly.
        result = self.bdd.false
        assignments = list(self.bdd.pick_iter(enabled_states))

        for assignment in assignments:
            # Create new marking by firing transition
            new_marking = set()

            # Copy current marking
            for place_id, var_name in self.place_vars.items():
                if assignment.get(var_name, False):
                    new_marking.add(place_id)

            # Remove tokens from input places
            for place_id in t.inputs:
                new_marking.discard(place_id)

            # Add tokens to output places
            for place_id in t.outputs:
                new_marking.add(place_id)

            # Encode new marking as BDD and add to result
            new_bdd = self.marking_to_bdd(frozenset(new_marking))
            result = result | new_bdd

        return result

    # ------------------------------------------------------------
    #  Reachability fixed point
    # ------------------------------------------------------------

    def compute_reachability(self):
        """
        Compute the set of reachable markings using fixed-point iteration.

        Returns:
            BDD representing all reachable markings
        """
        print("\nComputing reachability symbolically (BDD)...")

        # Initialize BDD variables
        self.initialize_bdd_variables()

        # Initial marking: places that are marked
        M0 = frozenset(p for p in self.model.places if self.model.places[p].marked)
        print(f"Initial marking: {sorted(M0)}")

        # Encode initial marking as BDD
        reach = self.marking_to_bdd(M0)

        # Fixed-point iteration
        iteration = 0
        while True:
            iteration += 1
            old_reach = reach

            # Compute image under all transitions
            new_states = self.bdd.false
            for tid in self.model.transitions:
                img = self.compute_image(reach, tid)
                new_states = new_states | img

            # Add new states
            reach = reach | new_states

            # Check for fixed point
            if reach == old_reach:
                print(f"Fixed point reached after {iteration} iterations")
                break

        self.reachable_bdd = reach

        # Count reachable markings (size of state space)
        self.num_reachable = int(self.bdd.count(reach, len(self.place_vars)))

        return reach

    # ------------------------------------------------------------
    #  High-level API
    # ------------------------------------------------------------

    def analyze(self) -> Dict:
        """
        Perform complete symbolic analysis.

        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()

        # Compute reachability
        reachable_bdd = self.compute_reachability()

        end_time = time.time()

        # Extract markings if state space is small enough
        if self.num_reachable <= 1000:
            reachable_markings: Optional[Set[Marking]] = self.bdd_to_markings(reachable_bdd)
        else:
            reachable_markings = None
            print(
                f"State space too large ({self.num_reachable} states), "
                f"not extracting individual markings"
            )

        results: Dict = {
            "method": "Symbolic (BDD)",
            "reachable_bdd": reachable_bdd,
            "reachable_markings": reachable_markings,
            "num_markings": self.num_reachable,
            "time_seconds": end_time - start_time,
            "bdd_node_count": len(self.bdd),
        }

        return results

    def print_results(self, results: Dict, model_name: str | None = None) -> None:
        """Print analysis results in a readable format."""
        title = "SYMBOLIC REACHABILITY ANALYSIS (BDD)"
        if model_name:
            title += f" – {model_name}"

        print(f"\n{'=' * 60}")
        print(title)
        print(f"{'=' * 60}")
        print(f"Number of reachable markings: {results['num_markings']}")
        print(f"BDD node count: {results['bdd_node_count']}")
        print(f"Computation time: {results['time_seconds']:.6f} seconds")

        markings = results.get("reachable_markings")
        if markings and len(markings) <= 20:
            print("\nAll reachable markings:")
            for marking in sorted(markings, key=lambda m: sorted(m)):
                print(f"  {sorted(marking)}")
        elif markings:
            print(f"\n(Showing first 10 of {len(markings)} markings)")
            for marking in sorted(markings, key=lambda m: sorted(m))[:10]:
                print(f"  {sorted(marking)}")

        print(f"{'=' * 60}\n")


__all__ = ["Marking", "SymbolicAnalyzer"]

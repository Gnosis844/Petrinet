# deadlock_testcases.py

from typing import List, Dict
from task4 import Transition


def build_deadlock_testcases():
    """
    Build a list of testcases for deadlock detection (Task 4).

    Each testcase is a dict with keys:
      - name: str
      - places: List[str]
      - transitions: List[Transition]
      - reachable_markings: List[Dict[str, int]]
      - expected_found: bool
      - expected_deadlocks: List[Dict[str, int]] (if expected_found is True)
    """

    testcases = []

    # -------------------------------------------------
    # Test 1: 4-place net (Start → InProgress → Done/Error)
    # -------------------------------------------------
    #
    # Places:
    #   p1: Start
    #   p2: InProgress
    #   p3: Done
    #   p4: Error
    #
    # Transitions:
    #   t1: p1 -> p2
    #   t2: p2 -> p3
    #   t3: p2 -> p4
    #
    # Initial marking M0 = (1,0,0,0)
    # Reachable:
    #   M0 = (1,0,0,0)
    #   M1 = (0,1,0,0)
    #   M2 = (0,0,1,0)   dead
    #   M3 = (0,0,0,1)   dead
    #
    places1 = ["p1", "p2", "p3", "p4"]
    transitions1 = [
        Transition(name="t1", pre=["p1"], post=["p2"]),
        Transition(name="t2", pre=["p2"], post=["p3"]),
        Transition(name="t3", pre=["p2"], post=["p4"]),
    ]
    reachable1 = [
        {"p1": 1, "p2": 0, "p3": 0, "p4": 0},  # M0
        {"p1": 0, "p2": 1, "p3": 0, "p4": 0},  # M1
        {"p1": 0, "p2": 0, "p3": 1, "p4": 0},  # M2 (dead)
        {"p1": 0, "p2": 0, "p3": 0, "p4": 1},  # M3 (dead)
    ]
    expected_deadlocks1 = [
        {"p1": 0, "p2": 0, "p3": 1, "p4": 0},
        {"p1": 0, "p2": 0, "p3": 0, "p4": 1},
    ]
    testcases.append(
        dict(
            name="Test 1 - Start/InProgress/Done/Error net",
            places=places1,
            transitions=transitions1,
            reachable_markings=reachable1,
            expected_found=True,
            expected_deadlocks=expected_deadlocks1,
        )
    )

    # -------------------------------------------------
    # Test 2: Simple loop, no deadlock
    # -------------------------------------------------
    #
    # Places:
    #   p1, p2
    #
    # Transitions:
    #   t1: p1 -> p2
    #   t2: p2 -> p1
    #
    # Initial: (1,0)
    # Reachable:
    #   (1,0), (0,1)
    # At (1,0): t1 enabled
    # At (0,1): t2 enabled
    # => No deadlock.
    #
    places2 = ["p1", "p2"]
    transitions2 = [
        Transition(name="t1", pre=["p1"], post=["p2"]),
        Transition(name="t2", pre=["p2"], post=["p1"]),
    ]
    reachable2 = [
        {"p1": 1, "p2": 0},
        {"p1": 0, "p2": 1},
    ]
    testcases.append(
        dict(
            name="Test 2 - Simple loop with no deadlock",
            places=places2,
            transitions=transitions2,
            reachable_markings=reachable2,
            expected_found=False,
            expected_deadlocks=[],
        )
    )

    # -------------------------------------------------
    # Test 3: No transitions at all (initial is dead)
    # -------------------------------------------------
    #
    # Places:
    #   p1
    # Transitions:
    #   (none)
    #
    # Initial marking: (1)
    # Reachable: only (1)
    # With no transitions, *every* marking is trivially dead
    # because there is no transition that could ever be enabled.
    #
    places3 = ["p1"]
    transitions3: List[Transition] = []
    reachable3 = [
        {"p1": 1},
    ]
    expected_deadlocks3 = [
        {"p1": 1},
    ]
    testcases.append(
        dict(
            name="Test 3 - No transitions (initial marking is dead)",
            places=places3,
            transitions=transitions3,
            reachable_markings=reachable3,
            expected_found=True,
            expected_deadlocks=expected_deadlocks3,
        )
    )

    # -------------------------------------------------
    # Test 4: Transition with empty preset (always enabled) -> no deadlock
    # -------------------------------------------------
    #
    # Places:
    #   p1
    # Transitions:
    #   t1: [] -> p1  (always enabled)
    #
    # Reachable markings (for the sake of the test):
    #   assume { (0), (1) }
    #
    # Because t1 has empty preset, it is always enabled => no dead marking.
    #
    places4 = ["p1"]
    transitions4 = [
        Transition(name="t1", pre=[], post=["p1"]),
    ]
    reachable4 = [
        {"p1": 0},
        {"p1": 1},
    ]
    testcases.append(
        dict(
            name="Test 4 - Always-enabled transition (empty preset)",
            places=places4,
            transitions=transitions4,
            reachable_markings=reachable4,
            expected_found=False,
            expected_deadlocks=[],
        )
    )

    # -------------------------------------------------
    # Test 5: Branching net with one non-trivial deadlock
    # -------------------------------------------------
    #
    # Places:
    #   p1: Start
    #   p2: BranchA
    #   p3: BranchB
    #   p4: Join
    #
    # Transitions:
    #   t1: p1 -> p2
    #   t2: p1 -> p3
    #   t3: p2 -> p4
    #   t4: p3 -> p4
    #
    # Initial: (1,0,0,0)
    # Example reachable markings (1-safe semantics, no double-branch concurrency):
    #   M0 = (1,0,0,0)
    #   M1 = (0,1,0,0)
    #   M2 = (0,0,1,0)
    #   M3 = (0,0,0,1)   dead
    #
    places5 = ["p1", "p2", "p3", "p4"]
    transitions5 = [
        Transition(name="t1", pre=["p1"], post=["p2"]),
        Transition(name="t2", pre=["p1"], post=["p3"]),
        Transition(name="t3", pre=["p2"], post=["p4"]),
        Transition(name="t4", pre=["p3"], post=["p4"]),
    ]
    reachable5 = [
        {"p1": 1, "p2": 0, "p3": 0, "p4": 0},  # M0
        {"p1": 0, "p2": 1, "p3": 0, "p4": 0},  # M1
        {"p1": 0, "p2": 0, "p3": 1, "p4": 0},  # M2
        {"p1": 0, "p2": 0, "p3": 0, "p4": 1},  # M3 (dead)
    ]
    expected_deadlocks5 = [
        {"p1": 0, "p2": 0, "p3": 0, "p4": 1},
    ]
    testcases.append(
        dict(
            name="Test 5 - Branching net with one deadlock",
            places=places5,
            transitions=transitions5,
            reachable_markings=reachable5,
            expected_found=True,
            expected_deadlocks=expected_deadlocks5,
        )
    )

    return testcases


# --------- helper functions for comparing markings ----------

def markings_equal(m1: Dict[str, int], m2: Dict[str, int]) -> bool:
    """Return True if two markings (dicts) are exactly equal."""
    return m1 == m2


def marking_in_list(m: Dict[str, int], candidates: List[Dict[str, int]]) -> bool:
    """Check if marking m is equal to one of the markings in candidates."""
    return any(markings_equal(m, c) for c in candidates)

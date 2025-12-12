"""
Main entry point: integrate Task 1–5 on Petri net PNML models.

For each PNML file:
  - Task 1: parse PNML -> PNModel
  - Task 2: explicit reachability (states, deadlocks)
  - Task 3: symbolic BDD reachability (states, BDD nodes)
  - Compare Task 2 vs Task 3:
      * number of reachable markings
      * (if small) check that reachable sets are equal
      * (if small) compare deadlock sets
  - Task 4: ILP-based deadlock detection over reachable markings
      * use BDD reachable set from Task 3 if available,
        otherwise fallback to explicit reachable markings
      * compare Task 4 deadlock with Task 2 deadlock
  - Task 5: optimization max c^T M, M in Reach(M0)
      * use state equation + BDD + no-good cuts (advanced version)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, FrozenSet
from datetime import datetime

from task1_PnmlParsing.pnml_parser import PNModel
from task2_ExplicitReachability.explicit_reachability import (
    Marking,
    explicit_reachability,
    find_deadlocks,
    is_enabled,
    run_explicit_analysis,
)
from task3_BddBasedReachability.bdd_reachability import SymbolicAnalyzer
from task4_IlpBddDeadlockDetection.deadlock_detection import DeadlockTransition, find_deadlock_with_ilp
from task5_ReachableOptimization.optimization import optimize_reachable


# -------------------------------------------------------------------
# Helpers to convert between representations
# -------------------------------------------------------------------

def marking_dict_to_frozenset(m: Dict[str, int]) -> FrozenSet[str]:
    """Convert marking dict {place_id: 0/1} to frozenset of marked place IDs."""
    return frozenset(p for p, v in m.items() if v == 1)


def markings_to_dict_list(
    markings: Set[Marking],
    places: List[str],
) -> List[Dict[str, int]]:
    """
    Convert a set of markings (frozenset of place IDs) to a list of
    dict[place_id -> 0/1], using a fixed place order.
    """
    result: List[Dict[str, int]] = []
    for M in markings:
        md = {p: (1 if p in M else 0) for p in places}
        result.append(md)
    return result


# -------------------------------------------------------------------
# Per-model pipeline
# -------------------------------------------------------------------

class TeeOutput:
    """Class to write output to both console and file."""
    def __init__(self, *files):
        self.files = files
    
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()


def analyze_model(pnml_path: Path) -> Optional[Dict]:
    """
    Run Task 1–5 on a single PNML model and print detailed results.

    Returns a summary dict for this model to be used in a global summary.
    """
    print("\n" + "=" * 80)
    print(f"MODEL: {pnml_path}")
    print("=" * 80)

    # ------------------------------
    # Task 1 – PNML parsing
    # ------------------------------
    model = PNModel.load_pnml(str(pnml_path))
    if model is None:
        print("[Error] Failed to parse PNML. Skipping this model.")
        return None

    model_name = pnml_path.name
    num_places = len(model.places)
    num_transitions = len(model.transitions)
    num_arcs = len(model.arcs)

    print(f"[Task 1] Parsed model: {num_places} places, "
          f"{num_transitions} transitions, {num_arcs} arcs")

    # ------------------------------
    # Task 2 – Explicit reachability
    # ------------------------------
    print("\n[Task 2] Explicit reachability analysis...")
    stats2 = run_explicit_analysis(model, model_name, print_details=False)

    # Recompute states/deadlocks explicitly for cross-checks
    states_explicit, edges_explicit = explicit_reachability(model)
    deadlocks_explicit = find_deadlocks(model, states_explicit)

    print(f"[Task 2] Reachable markings: {len(states_explicit)}")
    print(f"[Task 2] Deadlock markings: {len(deadlocks_explicit)}")

    # ------------------------------
    # Task 3 – Symbolic BDD reachability
    # ------------------------------
    print("\n[Task 3] Symbolic (BDD) reachability analysis...")
    analyzer = SymbolicAnalyzer(model)
    results3 = analyzer.analyze()
    analyzer.print_results(results3, model_name=model_name)

    num_markings_bdd = results3["num_markings"]
    num_bdd_nodes = results3["bdd_node_count"]
    markings_bdd: Optional[Set[Marking]] = results3["reachable_markings"]

    print(f"[Task 3] Reachable markings (BDD): {num_markings_bdd}")
    print(f"[Task 3] BDD node count: {num_bdd_nodes}")

    # ------------------------------
    # Compare Task 2 vs Task 3
    # ------------------------------
    print("\n[Compare Task 2 vs Task 3]")

    reach_sets_equal: Optional[bool] = None
    deadlocks_from_bdd: Optional[Set[Marking]] = None
    deadlock_sets_equal: Optional[bool] = None

    if markings_bdd is not None:
        # Compare reachable marking sets if have explicit enumeration from BDD
        if len(states_explicit) == num_markings_bdd:
            reach_sets_equal = set(states_explicit) == set(markings_bdd)
        else:
            reach_sets_equal = False

        # Compute deadlocks by scanning BDD reachable markings
        deadlocks_from_bdd_list: List[Marking] = []
        for M in markings_bdd:
            if not any(is_enabled(model, M, tid) for tid in model.transitions):
                deadlocks_from_bdd_list.append(M)
        deadlocks_from_bdd = set(deadlocks_from_bdd_list)
        deadlock_sets_equal = (deadlocks_from_bdd == set(deadlocks_explicit))

        print(f"  Reachable sets equal?   {reach_sets_equal}")
        print(f"  #Deadlocks (Task 2):    {len(deadlocks_explicit)}")
        print(f"  #Deadlocks (from BDD):  {len(deadlocks_from_bdd)}")
        print(f"  Deadlock sets equal?    {deadlock_sets_equal}")
    else:
        print("  BDD state space too large to extract all markings;")
        print("  skipping detailed set equality checks.")
        reach_sets_equal = None
        deadlocks_from_bdd = None
        deadlock_sets_equal = None

    # ------------------------------
    # Task 4 – ILP-based deadlock detection
    # ------------------------------
    print("\n[Task 4] ILP-based deadlock detection...")

    # Decide which reachable set to use for Task 4:
    # Prefer BDD markings (Task 3); if not available, fall back to explicit.
    if markings_bdd is not None:
        reachable_for_ilp: Set[Marking] = set(markings_bdd)
        source_for_ilp = "BDD (Task 3)"
    else:
        reachable_for_ilp = set(states_explicit)
        source_for_ilp = "Explicit (Task 2)"

    places_list = sorted(model.places.keys())

    # Convert markings to list of dicts for Task 4 ILP
    reachable_markings_list = markings_to_dict_list(reachable_for_ilp, places_list)

    # Build transitions for ILP
    transitions_ilp: List[DeadlockTransition] = []
    for tid, t in model.transitions.items():
        transitions_ilp.append(
            DeadlockTransition(
                name=tid,
                pre=list(t.inputs),
                post=list(t.outputs),
            )
        )

    found_deadlock_ilp, marking_ilp_dict = find_deadlock_with_ilp(
        places_list, transitions_ilp, reachable_markings_list
    )

    ilp_deadlock_marking_fs: Optional[Marking] = None
    ilp_marking_matches_explicit: Optional[bool] = None

    if found_deadlock_ilp and marking_ilp_dict is not None:
        ilp_deadlock_marking_fs = marking_dict_to_frozenset(marking_ilp_dict)
        print(f"  ILP found reachable deadlock (using {source_for_ilp}):")
        print(f"    marking dict: {marking_ilp_dict}")
        print(f"    marking set : {sorted(ilp_deadlock_marking_fs)}")

        # Cross-check with Task 2 deadlocks
        ilp_marking_matches_explicit = ilp_deadlock_marking_fs in set(deadlocks_explicit)
        print(f"  Matches one of Task 2 deadlocks? {ilp_marking_matches_explicit}")
    else:
        print(f"  ILP reports no reachable deadlock (using {source_for_ilp}).")
        ilp_marking_matches_explicit = (len(deadlocks_explicit) == 0)
        print(f"  Task 2 deadlocks empty? {len(deadlocks_explicit) == 0}")

    # ------------------------------
    # Task 5 – Optimization over reachable markings
    # ------------------------------
    print("\n[Task 5] Optimization max c^T M over Reach(M0)...")

    # Choose objective vector c similar to original Task 5 example:
    # - If this looks like a mutual-exclusion net (places starting with 'c'),
    #   give:  c_p = 10 for 'c*', 2 for 'r*', 1 otherwise.
    # - Else: c_p = 1 for all places.
    is_mutex_net = any(p.startswith("c") for p in model.places.keys())
    if is_mutex_net:
        c: Dict[str, int] = {}
        for p in sorted(model.places.keys()):
            if p.startswith("c"):
                c[p] = 10
            elif p.startswith("r"):
                c[p] = 2
            else:
                c[p] = 1
        objective_desc = (
            "10 * tokens in CS places + 2 * tokens in Request places + 1 * tokens in others."
        )
    else:
        c = {p: 1 for p in sorted(model.places.keys())}
        objective_desc = "Total number of tokens (c_p = 1 for all places)."

    print(f"  Objective: {objective_desc}")
    print(f"  Weights c: {c}")

    optimal_M5, log5 = optimize_reachable(model, c)
    print("\n[Task 5] Optimization log:")
    print(log5)

    objective_value5: Optional[int] = None
    if optimal_M5 is not None:
        objective_value5 = sum(c[p] * v for p, v in optimal_M5.items())
        print(f"[Task 5] Optimal reachable marking M*: {optimal_M5}")
        print(f"[Task 5] Max objective value c^T M*: {objective_value5}")
    else:
        print("[Task 5] No reachable optimal marking found (or ILP infeasible).")

    # ------------------------------
    # Build summary dictionary
    # ------------------------------
    summary: Dict = {
        "model_name": model_name,
        "num_places": num_places,
        "num_transitions": num_transitions,
        "num_arcs": num_arcs,
        "task2_num_states": len(states_explicit),
        "task2_num_deadlocks": len(deadlocks_explicit),
        "task3_num_states": num_markings_bdd,
        "task3_bdd_nodes": num_bdd_nodes,
        "task2_task3_reach_equal": reach_sets_equal,
        "task2_task3_deadlocks_equal": deadlock_sets_equal,
        "task4_ilp_found_deadlock": found_deadlock_ilp,
        "task4_ilp_matches_task2": ilp_marking_matches_explicit,
        "task5_objective_value": objective_value5,
    }

    return summary


# -------------------------------------------------------------------
# Global main: parse args, run pipeline on multiple models
# -------------------------------------------------------------------

def discover_testcases(testcases_dir: Path = Path("testcases"), 
                        filter_invalid: bool = True,
                        filter_type: Optional[str] = None) -> List[Path]:
    """
    Discover all PNML test case files in the testcases directory.
    
    Parameters
    ----------
    testcases_dir : Path
        Directory containing test case files
    filter_invalid : bool
        If True, exclude test cases with "invalid" in the filename
    filter_type : Optional[str]
        If provided, filter by type: "task1", "task2", "task3", "task4", "task5", "integration"
        If None, include all types
    
    Returns
    -------
    List[Path]
        Sorted list of test case file paths
    """
    if not testcases_dir.exists():
        return []
    
    # Find all .pnml files
    pnml_files = list(testcases_dir.glob("*.pnml"))
    
    # Filter invalid test cases if requested
    if filter_invalid:
        pnml_files = [f for f in pnml_files]
    
    # Filter by type if requested
    if filter_type:
        filter_type_lower = filter_type.lower()
        if filter_type_lower == "integration":
            pnml_files = [f for f in pnml_files if "integration" in f.name.lower()]
        elif filter_type_lower.startswith("task"):
            task_num = filter_type_lower.replace("task", "")
            pnml_files = [f for f in pnml_files if f"task{task_num}" in f.name.lower()]
        else:
            # Unknown filter type, return empty
            return []
    
    # Sort for consistent output
    pnml_files.sort(key=lambda p: p.name)
    
    return pnml_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MM BTL – Integrated Petri net analysis (Tasks 1–5)."
    )
    parser.add_argument(
        "models",
        nargs="*",
        help=(
            "PNML model files to analyze. "
            "If omitted, all valid test cases from testcases/ directory will be used."
        ),
    )
    parser.add_argument(
        "--testcases-dir",
        type=str,
        default="testcases",
        help="Directory containing test case files (default: testcases)",
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include invalid test cases (for testing error handling)",
    )
    parser.add_argument(
        "--filter-type",
        type=str,
        choices=["task1", "task2", "task3", "task4", "task5", "integration"],
        help="Filter test cases by type (task1-5 or integration)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path to write results (default: results_<timestamp>.txt)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress console output (only write to file)",
    )

    args = parser.parse_args()
    
    # Save original stdout
    original_stdout = sys.stdout
    
    # Setup output file
    if args.output:
        output_file_path = Path(args.output)
    else:
        output_file_path = Path(f"results.txt")
    
    # Open output file
    output_file = open(output_file_path, "w", encoding="utf-8")
    
    # Setup output redirection
    if args.quiet:
        # Only write to file
        sys.stdout = output_file
    else:
        # Write to both console and file
        sys.stdout = TeeOutput(original_stdout, output_file)
    
    # Print header with timestamp
    print("=" * 80)
    print(f"Petri Net Analysis - Tasks 1-5")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output file: {output_file_path}")
    print("=" * 80)
    print()

    if args.models:
        pnml_files = [Path(m) for m in args.models]
        print(f"Using specified PNML files ({len(pnml_files)} files):")
        for p in pnml_files:
            print(f"  - {p}")
    else:
        # Discover all valid test cases
        testcases_dir = Path(args.testcases_dir)
        pnml_files = discover_testcases(
            testcases_dir=testcases_dir,
            filter_invalid=not args.include_invalid,
            filter_type=args.filter_type
        )
        
        if not pnml_files:
            print(f"No test cases found in {testcases_dir}")
            if args.filter_type:
                print(f"  (filtered by type: {args.filter_type})")
            return
        
        filter_info = ""
        if args.filter_type:
            filter_info = f" (filtered: {args.filter_type})"
        if args.include_invalid:
            filter_info += " (including invalid)"
        
        print(f"Discovered {len(pnml_files)} test case(s) from {testcases_dir}{filter_info}:")
        for p in pnml_files:
            print(f"  - {p.name}")

    all_summaries: List[Dict] = []

    for pnml_path in pnml_files:
        if not pnml_path.exists():
            print(f"\n[Warning] PNML file not found: {pnml_path}, skipping.")
            continue

        summary = analyze_model(pnml_path)
        if summary is not None:
            all_summaries.append(summary)

    if not all_summaries:
        print("\nNo successful models analyzed. Exiting.")
        return

    # ------------------------------
    # Global summary table
    # ------------------------------
    print("\n" + "=" * 80)
    print("GLOBAL SUMMARY (Tasks 2, 3, 4, 5)")
    print("=" * 80)

    header = (
        f"{'Model':20s} "
        f"{'P':>3s} {'T':>3s} "
        f"{'T2_States':>9s} {'T2_Dead':>8s} "
        f"{'T3_States':>9s} {'BDD_Nodes':>10s} "
        f"{'T2=T3?':>7s} {'DeadEq?':>7s} "
        f"{'T4_OK?':>7s} {'T5_Obj':>8s}"
    )
    print(header)
    print("-" * len(header))

    for s in all_summaries:
        print(
            f"{s['model_name'][:20]:20s} "
            f"{s['num_places']:3d} {s['num_transitions']:3d} "
            f"{s['task2_num_states']:9d} {s['task2_num_deadlocks']:8d} "
            f"{s['task3_num_states']:9d} {s['task3_bdd_nodes']:10d} "
            f"{str(s['task2_task3_reach_equal']):>7s} {str(s['task2_task3_deadlocks_equal']):>7s} "
            f"{str(s['task4_ilp_matches_task2']):>7s} "
            f"{str(s['task5_objective_value']):>8s}"
        )

    print("=" * 80)
    
    # Print footer
    print()
    print("=" * 80)
    print(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total models analyzed: {len(all_summaries)}")
    print(f"Results saved to: {output_file_path}")
    print("=" * 80)
    
    # Close output file and restore stdout
    output_file.close()
    sys.stdout = original_stdout
    
    if not args.quiet:
        print(f"\nResults have been saved to: {output_file_path}")


if __name__ == "__main__":
    main()

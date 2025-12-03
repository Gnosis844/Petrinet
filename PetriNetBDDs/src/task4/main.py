# main.py

from task4 import find_deadlock_with_ilp
from testcases import (
    build_deadlock_testcases,
    marking_in_list,
)


if __name__ == "__main__":
    testcases = build_deadlock_testcases()
    total = len(testcases)
    passed = 0

    print(f"Running {total} deadlock-detection testcases for Task 4...\n")

    for idx, tc in enumerate(testcases, start=1):
        print(f"=== {tc['name']} (#{idx}) ===")

        places = tc["places"]
        transitions = tc["transitions"]
        reachable = tc["reachable_markings"]
        expected_found = tc["expected_found"]
        expected_deadlocks = tc["expected_deadlocks"]

        # Call Task 4 core function
        found, marking = find_deadlock_with_ilp(places, transitions, reachable)

        print(f"- Expected found : {expected_found}")
        print(f"- Solver found   : {found}")
        if found:
            print(f"- Deadlock marking found: {marking}")
        else:
            print(f"- Deadlock marking found: None")

        # Check correctness of this testcase
        ok = True
        if found != expected_found:
            ok = False
        else:
            if expected_found:
                # If we expect a deadlock, the returned marking must be one
                # of the expected deadlock markings.
                if not marking_in_list(marking, expected_deadlocks):
                    ok = False

        if ok:
            print("=> RESULT: PASS\n")
            passed += 1
        else:
            print("=> RESULT: FAIL\n")

    print(f"Summary: {passed}/{total} testcases passed.")

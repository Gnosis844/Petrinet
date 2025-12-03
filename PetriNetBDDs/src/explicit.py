from collections import deque
from pnml_parser import PNModel   # sử dụng Task 1


# ----------------------
#  Kiểm tra enabled
# ----------------------
def is_enabled(model, marking, tid):
    t = model.transitions[tid]
    # T enabled khi tất cả input places có token
    return all(p in marking for p in t.inputs)


# ----------------------
#  Firing transition
# ----------------------
def fire(model, marking, tid):
    t = model.transitions[tid]
    newM = set(marking)

    # remove tokens from input places
    for p in t.inputs:
        newM.remove(p)

    # add tokens to output places
    for p in t.outputs:
        newM.add(p)

    return frozenset(newM)


# ----------------------
#  EXPLORE EXPLICIT RG
# ----------------------
def explicit_reachability(model):
    M0 = frozenset(p for p in model.places if model.places[p].marked)

    visited = {M0}
    queue = deque([M0])
    edges = []   # (M, t, M')

    while queue:
        M = queue.popleft()

        for tid in model.transitions:
            if is_enabled(model, M, tid):
                M2 = fire(model, M, tid)
                edges.append((M, tid, M2))

                if M2 not in visited:
                    visited.add(M2)
                    queue.append(M2)

    return visited, edges


# ----------------------
#  MAIN TEST
# ----------------------
if __name__ == "__main__":
    model = PNModel.load_pnml("example.pnml")

    states, edges = explicit_reachability(model)

    print("\n===== EXPLICIT REACHABILITY =====")
    print("Reachable Markings:", len(states))

    for M, t, M2 in edges:
        print(f"{sorted(M)} --{t}--> {sorted(M2)}")

    print("\n===== DEADLOCK STATES =====")
    for M in states:
        enabled_list = [t for t in model.transitions if is_enabled(model, M, t)]
        if len(enabled_list) == 0:
            print("Deadlock:", sorted(M))

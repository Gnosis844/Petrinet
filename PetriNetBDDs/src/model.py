# model.py
"""
Core data structures and PNML parsing for Task 1.
- Place, Transition, PNModel
- PNModel.load_pnml(...) đọc PNML và build internal representation
- PNModel.validate() kiểm tra tính nhất quán (consistency) theo yêu cầu đề bài
"""

from lxml import etree


class Place:
    def __init__(self, pid: str, marked: bool = False):
        self.pid = pid
        self.marked = marked  # True iff initialMarking = 1
        self.inputs: list[str] = []   # transitions going into this place
        self.outputs: list[str] = []  # transitions going out of this place

    def __repr__(self) -> str:
        return f"Place(id={self.pid!r}, marked={self.marked})"


class Transition:
    def __init__(self, tid: str):
        self.tid = tid
        self.inputs: list[str] = []   # places → this transition
        self.outputs: list[str] = []  # this transition → places

    def __repr__(self) -> str:
        return f"Transition(id={self.tid!r})"


class PNModel:
    """
    Internal representation of a 1-safe Petri net.

    Attributes:
        places: dict[place_id, Place]
        transitions: dict[trans_id, Transition]
        arcs: list[(src_id, tgt_id)]
    """

    def __init__(self) -> None:
        self.places: dict[str, Place] = {}
        self.transitions: dict[str, Transition] = {}
        self.arcs: list[tuple[str, str]] = []

    # ------------------------------------------------------------------
    # Utility helpers used by later tasks
    # ------------------------------------------------------------------
    def initial_marking(self) -> frozenset[str]:
        """Return the initial marking as a frozenset of place IDs."""
        return frozenset(p_id for p_id, p in self.places.items() if p.marked)

    # ------------------------------------------------------------------
    # Consistency check (phần "verify consistency" của Task 1)
    # ------------------------------------------------------------------
    def validate(self) -> list[str]:
        """
        Check simple consistency constraints required in the assignment:
        - Every arc's source/target must refer to an existing place or transition.

        Returns:
            A list of error messages. Empty list means the model is consistent.
        """
        errors: list[str] = []

        all_node_ids = set(self.places.keys()) | set(self.transitions.keys())

        for (src, tgt) in self.arcs:
            if src not in all_node_ids:
                errors.append(f"Arc ({src} -> {tgt}) has unknown source node '{src}'.")
            if tgt not in all_node_ids:
                errors.append(f"Arc ({src} -> {tgt}) has unknown target node '{tgt}'.")

        # Bạn có thể bổ sung thêm các check khác nếu muốn, ví dụ:
        # - Node không có incident arcs (cô đơn)
        # - Transition không có input hoặc không có output, v.v.

        return errors

    # ------------------------------------------------------------------
    # PNML loader (Task 1)
    # ------------------------------------------------------------------
    @staticmethod
    def load_pnml(path: str) -> "PNModel | None":
        """
        Parse a PNML file into a PNModel.

        Returns:
            PNModel object if parsing & validation succeed, otherwise None.
        """
        print(f"Loading PNML file: {path}")
        model = PNModel()

        # Parse XML
        try:
            xml_root = etree.parse(path).getroot()
        except Exception as e:
            print(f"[ERROR] While parsing PNML: {e}")
            return None

        # Detect namespace (default PNML namespace)
        ns = xml_root.nsmap.get(None, "http://www.pnml.org/version-2009/grammar/pnml")
        nsmap = {"ns": ns}

        # -------------------
        # Parse places
        # -------------------
        for p in xml_root.xpath(".//ns:place", namespaces=nsmap):
            pid = p.get("id")
            init_mk = p.xpath(".//ns:initialMarking/ns:text/text()", namespaces=nsmap)
            has_token = bool(init_mk and init_mk[0].strip() == "1")
            model.places[pid] = Place(pid, marked=has_token)

        # -------------------
        # Parse transitions
        # -------------------
        for t in xml_root.xpath(".//ns:transition", namespaces=nsmap):
            tid = t.get("id")
            model.transitions[tid] = Transition(tid)

        # -------------------
        # Parse arcs (source, target)
        # -------------------
        for a in xml_root.xpath(".//ns:arc", namespaces=nsmap):
            src = a.get("source")
            tgt = a.get("target")
            model.arcs.append((src, tgt))

        # -------------------
        # Build input/output relations
        # -------------------
        for src, tgt in model.arcs:
            if src in model.places and tgt in model.transitions:
                # place → transition
                model.places[src].outputs.append(tgt)
                model.transitions[tgt].inputs.append(src)
            elif src in model.transitions and tgt in model.places:
                # transition → place
                model.transitions[src].outputs.append(tgt)
                model.places[tgt].inputs.append(src)
            # Nếu src/tgt không tồn tại, phần validate() sẽ bắt lỗi.

        # -------------------
        # Consistency check
        # -------------------
        errors = model.validate()
        if errors:
            print("[ERROR] PNML model is inconsistent:")
            for msg in errors:
                print("  -", msg)
            return None

        print("PNML parsed successfully.")
        print(f"Places: {len(model.places)} | "
              f"Transitions: {len(model.transitions)} | "
              f"Arcs: {len(model.arcs)}")

        return model

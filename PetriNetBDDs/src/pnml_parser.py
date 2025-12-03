"""
pnml_parser.py - Python-compatible module name
This is a copy of pnml-parser.py with a proper Python module name.
Uses lxml as in the original.
"""

from lxml import etree
import sys

class Place:
    def __init__(self, pid, marked=False):
        self.pid = pid
        self.marked = marked
        self.inputs = []
        self.outputs = []

class Transition:
    def __init__(self, tid):
        self.tid = tid
        self.inputs = []
        self.outputs = []

class PNModel:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = []

    @staticmethod
    def load_pnml(path):
        print(f"Loading PNML file: {path}")
        model = PNModel()

        # Parse XML
        try:
            xml = etree.parse(path).getroot()
        except Exception as e:
            print("Error while parsing PNML:", e)
            return None

        # Detect namespace
        ns = xml.nsmap.get(None, "http://www.pnml.org/version-2009/grammar/pnml")

        # Parse places
        for p in xml.xpath(".//ns:place", namespaces={"ns": ns}):
            pid = p.get("id")
            init_mk = p.xpath(".//ns:initialMarking/ns:text/text()", namespaces={"ns": ns})
            has_token = (init_mk and init_mk[0].strip() == "1")
            model.places[pid] = Place(pid, marked=has_token)

        # Parse transitions
        for t in xml.xpath(".//ns:transition", namespaces={"ns": ns}):
            tid = t.get("id")
            model.transitions[tid] = Transition(tid)

        # Parse arcs
        for a in xml.xpath(".//ns:arc", namespaces={"ns": ns}):
            src = a.get("source")
            tgt = a.get("target")
            model.arcs.append((src, tgt))

        # Build input/output relations
        for src, tgt in model.arcs:
            if src in model.places and tgt in model.transitions:
                model.places[src].outputs.append(tgt)
                model.transitions[tgt].inputs.append(src)
            elif src in model.transitions and tgt in model.places:
                model.transitions[src].outputs.append(tgt)
                model.places[tgt].inputs.append(src)

        print("PNML parsed successfully.")
        print(f"Places: {len(model.places)} | Transitions: {len(model.transitions)} | Arcs: {len(model.arcs)}")
        return model


# ===============================
# MAIN EXECUTION 
# ===============================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pnml_parser.py <file.pnml>")
        sys.exit(0)

    filepath = sys.argv[1]
    model = PNModel.load_pnml(filepath)

    if model:
        print("\n=== Model Summary ===")
        print("Places:")
        for p in model.places.values():
            print(f"  {p.pid} (token={p.marked})")
        print("Transitions:")
        for t in model.transitions.values():
            print(f"  {t.tid}")
        print("Arcs:")
        for a in model.arcs:
            print(f"  {a[0]} -> {a[1]}")

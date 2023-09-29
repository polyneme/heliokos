import json
from pathlib import Path

from rdflib import Graph
from toolz import merge

RDFA_CORE_INITIAL_CONTEXT = json.loads(
    Path(__file__).parent.joinpath("rdfa11.json").read_text()
)


class RDFGraphRepo:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def as_rdflib_graph(self):
        g = Graph(bind_namespaces="rdflib")
        for c in self.items:
            if "@context" not in c:
                c = merge(c, RDFA_CORE_INITIAL_CONTEXT)
            g.parse(data=c, format="json-ld")
        return g

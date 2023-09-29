import json
import uuid
from copy import deepcopy

import rdflib
from toolz import merge

from heliokos.infra.constants import RDFA_CORE_INITIAL_CONTEXT


def build_concept(data):
    concept = deepcopy(data)
    concept["@id"] = str(uuid.uuid4())
    return concept


class ConceptRepo:
    def __init__(self):
        self.concepts = []

    def add(self, concept):
        self.concepts.append(concept)

    def as_rdflib_graph(self):
        g = rdflib.Graph(bind_namespaces="rdflib")
        for c in self.concepts:
            if "@context" not in c:
                c = merge(c, RDFA_CORE_INITIAL_CONTEXT)
            g.parse(data=c, format="json-ld")
        return g


def test_concept():
    repo = ConceptRepo()
    repo.add(build_concept({"skos:prefLabel": "Solar wind"}))
    g = repo.as_rdflib_graph()
    assert any(
        g.triples((None, rdflib.namespace.SKOS.prefLabel, rdflib.Literal("Solar wind")))
    )

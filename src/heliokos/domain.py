import json
import uuid
from copy import deepcopy

from rdflib.namespace import SKOS
from rdflib import Literal

from heliokos.infra.core import RDFGraphRepo


def build_concept(data):
    concept = deepcopy(data)
    concept["@id"] = str(uuid.uuid4())
    return concept


class ConceptRepo(RDFGraphRepo):
    def __init__(self):
        super().__init__()


def test_concept():
    repo = ConceptRepo()
    repo.add(build_concept({"skos:prefLabel": "Solar wind"}))
    g = repo.as_rdflib_graph()
    assert any(g.triples((None, SKOS.prefLabel, Literal("Solar wind"))))

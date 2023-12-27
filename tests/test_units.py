"""
Unit tests.
"""
from rdflib import SKOS, Literal

from heliokos.domain.core import ConceptScheme
from heliokos.infra.core import Concept


def test_concept_scheme():
    scheme = ConceptScheme().add(Concept("Solar wind"))
    assert any(scheme.g.triples((None, SKOS.prefLabel, Literal("Solar wind"))))


def test_narrower():
    physics = Concept("Physics")
    plasma = Concept("Plasma")
    cs = (
        ConceptScheme().add(physics).add(plasma).connect(physics, plasma, SKOS.narrower)
    )
    assert cs.g.value(cs.local_id_for(physics.uri), SKOS.narrower) == cs.local_id_for(
        plasma.uri
    )

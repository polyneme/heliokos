"""
Unit tests.
"""

from heliokos.domain.core import Concept, ConceptScheme, SKOS, Literal


def test_concept_scheme():
    scheme = ConceptScheme().add(Concept("Solar wind"))
    assert any(scheme.g.triples((None, SKOS.prefLabel, Literal("Solar wind"))))


def test_narrower():
    physics = Concept("Physics")
    plasma = Concept("Plasma")
    cs = (
        ConceptScheme().add(physics).add(plasma).connect(physics, plasma, SKOS.narrower)
    )
    assert cs.g.value(cs.local_id_for(physics.id), SKOS.narrower) == cs.local_id_for(
        plasma.id
    )

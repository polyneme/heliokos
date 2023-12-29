"""
Unit tests.
"""
import tempfile
from pathlib import Path

from rdflib import SKOS, Literal, Graph

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
    assert cs.g.value(physics.uri, SKOS.narrower) == plasma.uri


def test_concept_scheme_top_concept():
    concept = Concept("Solar wind")
    scheme = ConceptScheme().add(concept).set_as_top_concept(concept)
    assert (scheme.uri, SKOS.hasTopConcept, concept.uri) in scheme.g


def test_concept_scheme_export_as_ttl():
    # Create a scheme with one top concept
    physics = Concept("Physics")
    scheme = ConceptScheme().add(physics).set_as_top_concept(physics)
    # and two additional concepts,
    astrophysics = Concept("Astrophysics")
    heliophysics = Concept("Heliophysics")
    scheme.add(astrophysics).add(heliophysics)
    # both of which are directly narrower than the top concept.
    scheme.connect(physics, astrophysics, SKOS.narrower)
    scheme.connect(physics, heliophysics, SKOS.narrower)
    # Export this concept scheme to a Turtle file.
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = f"{tmpdir}/scheme.ttl"
        scheme.to_file(filename)
        g = Graph()
        g.parse(filename)
        assert set(g) == set(scheme.g)

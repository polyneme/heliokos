"""
Unit tests.
"""

from heliokos.domain.core import Concept, ConceptRepo, SKOS, Literal


def test_narrower():
    physics = Concept()
    physics.pref_label = "Physics"
    plasma = Concept()
    plasma.pref_label = "Plasma"
    physics.add_narrower(plasma)
    repo = ConceptRepo()
    repo.add(physics)
    repo.add(plasma)
    assert repo.g.value(physics.id, SKOS.narrower) == plasma.id


def test_concept_repo():
    repo = ConceptRepo()
    solar_wind = Concept()
    solar_wind.pref_label = "Solar wind"
    repo.add(solar_wind)
    assert any(repo.g.triples((None, SKOS.prefLabel, Literal("Solar wind"))))

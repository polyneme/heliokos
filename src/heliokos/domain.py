from rdflib.namespace import SKOS
from rdflib import Literal

from heliokos.infra.core import (
    RDFGraphRepo,
    RDFGraphDocument,
)


class Concept(RDFGraphDocument):
    """
    Represent a skos:Concept.

    Support setting skos:narrower only, with skos:broader inferrable.
    Rationale: https://www.w3.org/TR/vocab-data-cube/#schemes-hierarchy
    """

    def __init__(self):
        super().__init__()

    @property
    def pref_label(self):
        return self.g.value(self.id, SKOS.prefLabel)

    @pref_label.setter
    def pref_label(self, s):
        self.g.add((self.id, SKOS.prefLabel, Literal(s)))

    @property
    def alt_labels(self):
        return list(self.g.objects(self.id, SKOS.altLabel))

    def add_alt_label(self, s):
        self.g.add((self.id, SKOS.altLabel, Literal(s)))

    @property
    def narrower(self):
        return list(self.g.objects(self.id, SKOS.narrower))

    def add_narrower(self, concept: "Concept"):
        self.g.add((self.id, SKOS.narrower, concept.id))


class ConceptRepo(RDFGraphRepo):
    def __init__(self):
        super().__init__()


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

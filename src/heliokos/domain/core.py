from pathlib import Path

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

    def __init__(self, init_data=None):
        super().__init__(init_data)

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


class ConceptScheme:
    pass


class Harmonization:
    pass


class Corpus:
    pass


class GroundTruth:
    pass


class SearchIndex:
    pass


class ConceptRepo(RDFGraphRepo):
    def __init__(self):
        super().__init__()


core_repo = RDFGraphRepo()
for ttl_file in Path(__file__).parent.glob("*.ttl"):
    core_repo.add_from_file(ttl_file)
for ttl_file in Path(__file__).parent.parent.joinpath("infra").glob("rd*.ttl"):
    core_repo.add_from_file(ttl_file)

from pathlib import Path

from rdflib.namespace import SKOS, OWL
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

    def __init__(self, pref_label=None):
        super().__init__()
        if pref_label is not None:
            self.g.add((self.id, SKOS.prefLabel, Literal(pref_label)))

    @property
    def pref_label(self):
        return self.g.value(subject=self.id, predicate=SKOS.prefLabel)


class ConceptScheme(RDFGraphRepo):
    def __init__(self):
        super().__init__()

    def copy(self):
        me_copy = ConceptScheme()
        for triple in self.g:
            me_copy.g.add(triple)
        return me_copy

    def add(self, concept):
        me_copy = self.copy()
        local_concept = Concept(str(concept.pref_label))
        me_copy.g.add((local_concept.id, SKOS.prefLabel, local_concept.pref_label))
        me_copy.g.add((local_concept.id, OWL.sameAs, concept.id))
        return me_copy

    def connect(self, concept_1, concept_2, property_=SKOS.related):
        me_copy = self.copy()
        me_copy.g.add((concept_1.id, property_, concept_2.id))
        return me_copy

    def local_id_for(self, id_):
        return self.g.value(subject=None, predicate=OWL.sameAs, object=id_)


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


# core_repo = RDFGraphRepo()
# for ttl_file in Path(__file__).parent.glob("*.ttl"):
#     core_repo.add_from_file(ttl_file)
# for ttl_file in Path(__file__).parent.parent.joinpath("infra").glob("rd*.ttl"):
#     core_repo.add_from_file(ttl_file)

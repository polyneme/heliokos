from pathlib import Path

from rdflib.namespace import SKOS, OWL, RDF
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

    def __init__(self, data=None):
        if data is None:
            init_data = {"@type": "skos:Concept"}
        elif isinstance(data, str):
            init_data = {"@type": "skos:Concept", "skos:prefLabel": data}
        else:
            init_data = data
        super().__init__(init_data)

    @property
    def pref_label(self):
        return self.g.value(subject=self.id, predicate=SKOS.prefLabel)


class ConceptScheme(RDFGraphRepo):
    @classmethod
    def from_file(cls, filepath: str = "domain/helioregion.ttl"):
        if not filepath.startswith("/"):
            # relative to `helioweb` module
            filepath = Path(__file__).parent.parent.joinpath(filepath)
        scheme = ConceptScheme()
        scheme.add_graph_from_file(filepath)
        return scheme

    def __init__(self):
        super().__init__()
        me_doc = RDFGraphDocument()
        self.add_graph_document(me_doc)
        self.g.add((me_doc.id, RDF.type, SKOS.ConceptScheme))

    def add(self, concept, is_top_concept=False):
        me_copy = self.copy()
        local_concept = Concept(str(concept.pref_label))
        me_copy.add_graph_document(local_concept)
        scheme_id = me_copy.g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
        me_copy.g.add((local_concept.id, SKOS.inScheme, scheme_id))
        if is_top_concept:
            me_copy.g.add((scheme_id, SKOS.hasTopConcept, local_concept.id))
        me_copy.g.add((local_concept.id, OWL.sameAs, concept.id))
        return me_copy

    def connect(self, concept_1, concept_2, property_=SKOS.related):
        allowed = {SKOS.narrower, SKOS.related}
        if property_ not in allowed:
            raise ValueError(f"`property_` must be in {allowed}")
        me_copy = self.copy()
        me_copy.g.add(
            (
                self.local_id_for_concept(concept_1),
                property_,
                self.local_id_for_concept(concept_2),
            )
        )
        return me_copy

    def find_one(self, pref_label: str) -> Concept:
        cid = self.g.value(predicate=SKOS.prefLabel, object=Literal(pref_label))
        return Concept(self.graph_document_by_id(cid)) if cid is not None else None


class Harmonization(RDFGraphRepo):
    def __init__(self):
        super().__init__()

    def add(self, concept_scheme: ConceptScheme):
        me_copy = self.copy()
        for triple in concept_scheme.g:
            me_copy.g.add(triple)
        return me_copy

    def connect(self, concept_1, concept_2, property_=SKOS.relatedMatch):
        allowed = {
            SKOS.closeMatch,
            SKOS.exactMatch,
            SKOS.narrowMatch,
            SKOS.relatedMatch,
        }
        if property_ not in allowed:
            raise ValueError(f"`property_` must be in {allowed}")
        me_copy = self.copy()
        me_copy.g.add(
            (
                self.local_id_for_concept(concept_1),
                property_,
                self.local_id_for_concept(concept_2),
            )
        )
        return me_copy

    def narrowmatch_bridge(self, concept_1, concept_2):
        c1 = self.local_id_for_concept(concept_1).n3()
        c2 = self.local_id_for_concept(concept_2).n3()
        qres = self.g.query(
            f"""
        SELECT ?c1label ?c4label
        WHERE {{
         {c1} skos:narrower*/(skos:narrowMatch|skos:exactMatch)/skos:narrower* {c2} .
        }}
        """,
            initNs={"skos": SKOS},
        )
        return len(qres) != 0


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

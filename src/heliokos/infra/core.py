import json
from collections import defaultdict
from datetime import datetime
from itertools import permutations
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

from bson import ObjectId
from pymongo import MongoClient, UpdateOne
from rdflib import Graph, URIRef, XSD, Literal
from rdflib.namespace import SKOS, RDFS, RDF
from toolz import merge, merge_with

from heliokos.infra.config import MONGO_HOST, MONGO_USER, MONGO_PASSWORD, MONGO_TLS

RDFA_CORE_INITIAL_CONTEXT = json.loads(
    Path(__file__).parent.joinpath("static/rdfa11.json").read_text()
)

CONTEXT_BASE = RDFA_CORE_INITIAL_CONTEXT["@context"]["@base"]


def core_context_prefix_map():
    return {k: v for k, v in RDFA_CORE_INITIAL_CONTEXT["@context"].items()}


def with_core_context(d):
    return merge(d, RDFA_CORE_INITIAL_CONTEXT)


def with_oid_id(d):
    return merge(d, {"@id": str(ObjectId())})


class ValidationError(Exception):
    pass


class GraphDocument:
    """
    A graph fragment where there is one and only one "root" subject.
    """

    def __init__(self, data=None):
        self.g = Graph()
        init_data = {} if data is None else data
        if len(init_data) == 0:
            init_data = with_oid_id(with_core_context({"@type": "rdfs:Resource"}))
        if "@context" not in init_data:
            init_data = with_core_context(init_data)
        if "@id" not in init_data:
            init_data = with_oid_id(init_data)
        if "@type" not in init_data:
            init_data["@type"] = "rdfs:Resource"
        self.g.parse(
            data=init_data,
            format="json-ld",
        )
        self.uri = str(next(self.g.subjects()))
        self.check()

    def check(self):
        if len(list(self.g.subjects(unique=True))) != 1:
            raise ValidationError(
                f"document '{self.label} ({self.uri})' has more than one subject"
            )

    @property
    def id_suffix(self):
        return self.uri.split("/")[-1]

    @property
    def label(self):
        rv = self.g.value(URIRef(self.uri), SKOS.prefLabel)
        if rv is None:
            rv = self.g.value(URIRef(self.uri), RDFS.label)
        if rv is None:
            rv = f"@id={self.uri}"
        return rv

    def update(self, doc):
        self.g.parse(data=doc, format="json-ld")
        self.check()
        return self

    def to_dict(self):
        return json.loads(self.g.serialize(format="json-ld"))[0]

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.to_dict() == other.to_dict()

    @classmethod
    def from_file(cls, filepath: Path):
        rv = cls()
        rv.g = Graph()
        rv.g.parse(filepath)
        rv.uri = str(next(rv.g.subjects()))
        rv.check()
        return rv

    def to_file(self):
        Path(".document").mkdir(exist_ok=True)
        self.g.serialize(f".document/{quote_plus(self.uri)}.ttl")


def get_mongodb():
    client = MongoClient(
        host=MONGO_HOST, username=MONGO_USER, password=MONGO_PASSWORD, tls=MONGO_TLS
    )
    mdb = client.heliokos
    return mdb


has_literal_range = {SKOS.prefLabel, SKOS.altLabel}


def datetime_now():
    return datetime.now(tz=ZoneInfo("America/New_York"))


_collection = get_mongodb()["nodes"]
_collection.create_index({"g": 1, "s": 1, "edge.p": 1, "edge.o": 1})
_collection.create_index({"g": 1, "edge.p": 1, "edge.o": 1, "s": 1})
_collection.create_index({"edge.p": 1, "edge.o": 1, "s": 1, "g": 1})


class GraphRepo:
    """An interface to a named graph."""

    def __init__(self, uri=None):
        if uri is None:
            uri = f"{CONTEXT_BASE}{ObjectId()}"
        self.uri = str(uri)
        self.filter = {"g": uri}
        self.coll = get_mongodb()["nodes"]

    def merge_rdflib_graph(self, g: Graph):
        s_edge = defaultdict(list)
        for s, p, o in g:
            s, p = str(s), str(p)
            if isinstance(o, Literal):
                match o.datatype:
                    case dt if dt == XSD.integer:
                        o = int(o.value)
                    case dt if dt == XSD.double:
                        o = float(o.value)
                    case _:
                        o = str(o)
            else:
                o = str(o)

            s_edge[s].append({"p": p, "o": o})
        now = datetime_now()
        updates = [
            {
                "filter": merge(self.filter, {"s": s}),
                "update": {
                    "$set": {"g": self.uri, "s": s, "edge": edge, "env.lu": now}
                },
                "upsert": True,
            }
            for s, edge in s_edge.items()
        ]
        bulk_write_result = self.coll.bulk_write([UpdateOne(**u) for u in updates])
        return {
            f"subjects_{k}": getattr(bulk_write_result, k)
            for k in (
                "modified_count",
                "upserted_count",
            )
        }

    def merge_graph_document(self, gdoc: GraphDocument):
        doc = gdoc.to_dict()
        now = datetime_now()
        update = {
            "$set": {
                "g": self.uri,
                "s": doc["@id"],
                "edge": [
                    {"p": "a" if p == "@type" else p, "o": o}
                    for p, o in doc.items()
                    if p != "@id"
                ],
                "env.lu": now,
            }
        }
        self.coll.update_one(
            merge(self.filter, {"s": update["$set"]["s"]}), update, upsert=True
        )

    def merge_graph_from_file(self, filepath: Path):
        if not str(filepath).startswith("/"):
            # relative to `helioweb` project root dir
            filepath = Path(__file__).parent.parent.parent.parent.joinpath(filepath)
        g = Graph()
        g.parse(filepath)
        self.merge_rdflib_graph(g)

    def to_rdflib_graph(self):
        g = Graph()
        for s_doc in self.coll.find(self.filter, ["s", "edge"]):
            for s_edge in s_doc["edge"]:
                s_edge_p = URIRef(s_edge["p"])
                s_edge_o = (
                    Literal(s_edge["o"])
                    if s_edge_p in has_literal_range
                    else URIRef(s_edge["o"])
                )
                g.add((URIRef(s_doc["s"]), s_edge_p, s_edge_o))
        return g

    def subjects(self):
        return self.coll.distinct("s", self.filter)

    def to_file(self):
        Path(".graph").mkdir(exist_ok=True)
        self.to_rdflib_graph().serialize(f".graph/{quote_plus(self.uri)}.ttl")

    def set_edge(self, s, p, o):
        s, p = str(s), str(p)
        o = str(o) if isinstance(o, (str, URIRef)) else o.value
        self.coll.update_one(
            merge(self.filter, {"s": s}),
            {"$addToSet": {"edge": {"p": p, "o": o}}},
        )

    def graph_document_for(self, subject):
        rdoc = self.coll.find_one(merge(self.filter, {"s": URIRef(subject)}))
        if rdoc is None:
            raise ValueError(f"no subject {subject}")
        types = []
        other_edges = []
        for e in rdoc["edge"]:
            if e["p"] in ("a", "rdf:type"):
                types.append(e["o"])
            else:
                other_edges.append({e["p"]: e["o"]})

        gbase = {"@id": rdoc["s"], "@type": types}
        gdoc = merge_with(list, *([gbase] + other_edges))
        return GraphDocument(data=gdoc)


CONCEPT_RELATIONS_ALLOWED = {SKOS.narrower, SKOS.related}


class ConceptRepo(GraphRepo):
    def __init__(self, uri=None):
        super().__init__(uri=uri)


class Concept:
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
            init_data = merge(data, {"@type": "skos:Concept"})
        self.gd = GraphDocument(init_data)

    @property
    def pref_label(self):
        return self.gd.g.value(subject=URIRef(self.gd.uri), predicate=SKOS.prefLabel)


class ConceptScheme:
    def __init__(self, uri=None):
        self.repo = GraphRepo()
        if uri is None:
            uri = f"{CONTEXT_BASE}{ObjectId()}"
        self.uri = str(uri)
        self.repo.merge_graph_document(
            GraphDocument({"@id": self.uri, "@type": "skos:ConceptScheme"})
        )

    @classmethod
    def from_file(cls, filepath: Path):
        g = Graph()
        g.parse(filepath)
        uri = g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
        rv = cls(uri=uri)
        rv.repo = GraphRepo(uri=uri)
        rv.repo.merge_rdflib_graph(g)
        return rv

    @property
    def uri_suffix(self):
        return self.uri.split("/")[-1]

    def add(self, concept: Concept):
        gdoc = GraphDocument(merge(concept.to_dict(), {"skos:inScheme": self.uri}))
        self.repo.merge_graph_document(gdoc)
        return self

    def set_as_top_concept(self, concept: Concept):
        self.repo.set_edge(self.uri, "skos:hasTopConcept", concept.uri)

    def connect(self, concept_1, concept_2, property_=SKOS.related):
        if property_ not in CONCEPT_RELATIONS_ALLOWED:
            raise ValueError(f"`property_` must be in {CONCEPT_RELATIONS_ALLOWED}")
        self.repo.set_edge(concept_1.uri, property_, concept_2.uri)

    def find_by_pref_label(self, pref_label):
        if isinstance(key, str):
            cid = self.g.value(predicate=SKOS.prefLabel, object=Literal(key))

    def find_one_by_id(self, id_) -> Concept:
        return Concept(self.repo.graph_document_for(id_))

    def to_file(self):
        me_id = self.g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
        Path(".scheme").mkdir(exist_ok=True)
        self.g.serialize(f".scheme/{me_id.split('/')[-1]}.ttl")

    @property
    def concepts(self):
        rv = []
        for id_, pref_label in self.repo.to_rdflib_graph().query(
            f"""
                SELECT ?ogc ?clabel
                WHERE {{
                ?c a skos:Concept .
                ?c owl:sameAs ?ogc .
                ?c skos:inScheme <{self.uri}> .
                ?c skos:prefLabel ?clabel
                }}""",
            initNs={"skos": SKOS},
        ):
            rv.append(Concept({"@id": str(id_), "skos:prefLabel": pref_label}))
        return rv

    @property
    def relations(self) -> list[list[URIRef]]:
        rv = []
        relation_values = " ".join([f"<{r}>" for r in CONCEPT_RELATIONS_ALLOWED])
        query = f"""
        SELECT ?ogs ?relation ?ogo
            WHERE {{
                VALUES ?relation {{ {relation_values} }}
                ?s ?relation ?o .
                ?s a skos:Concept; owl:sameAs ?ogs; skos:inScheme <{self.id}> .
                ?o a skos:Concept; skos:inScheme <{self.id}>; owl:sameAs ?ogo .
            }}"""
        for s_id, relation, o_id in self.g.query(
            query,
            initNs={"skos": SKOS},
        ):
            rv.append([s_id, relation, o_id])
        return rv

    @property
    def deny_relations(self):
        """List of relations to deny.

        if (?a SKOS.narrower+ ?b) then deny [
          (?a SKOS.narrower ?b)
          (b? SKOS.narrower ?a),
          (a? SKOS.related ?b),
          (b? SKOS.related ?a),
        ] .
        if (?a SKOS.related ?b) then deny [
          (?a SKOS.narrower ?b),
          (?b SKOS.narrower ?a),
        ]
        if (a? SKOS.narrower+ ?b . a? SKOS.related ?c OR ?c SKOS.related ?a) then deny [
          (b? SKOS.narrower ?c),
        ] .
        """
        rv = []
        current_relations = self.relations
        query_narrow_transitive = f"""
        SELECT ?oga ?ogb
            WHERE {{
                ?a skos:narrower+ ?b .
                ?a a skos:Concept; owl:sameAs ?oga; skos:inScheme <{self.uri}> .
                ?b a skos:Concept; owl:sameAs ?ogb; skos:inScheme <{self.uri}> .
            }}"""
        for oga, ogb in self.g.query(query_narrow_transitive, initNs={"skos": SKOS}):
            for c1, c2 in permutations([oga, ogb]):
                for p in [SKOS.related, SKOS.narrower]:
                    rv.append([c1, p, c2])
        # current relations are redundant to include
        rv = [denied for denied in rv if denied not in current_relations]

        query_related = f"""
        SELECT ?oga ?ogb
            WHERE {{
                ?a skos:related ?b .
                ?a a skos:Concept; owl:sameAs ?oga; skos:inScheme <{self.uri}> .
                ?b a skos:Concept; owl:sameAs ?ogb; skos:inScheme <{self.uri}> .
            }}"""
        for oga, ogb in self.g.query(query_related, initNs={"skos": SKOS}):
            for c1, c2 in permutations([oga, ogb]):
                rv.append(
                    [c1, SKOS.narrower, c2],
                )

        query_narrow_transitive_with_related = f"""
        SELECT ?oga ?ogb ?ogc
            WHERE {{
                ?a skos:narrower+ ?b .
                ?a skos:related|^skos:related ?c .
                ?a a skos:Concept; owl:sameAs ?oga; skos:inScheme <{self.uri}> .
                ?b a skos:Concept; owl:sameAs ?ogb; skos:inScheme <{self.uri}> .
                ?c a skos:Concept; owl:sameAs ?ogc; skos:inScheme <{self.uri}> .
            }}"""
        for oga, ogb, ogc in self.repo.to_rdflib_graph().query(
            query_narrow_transitive_with_related, initNs={"skos": SKOS}
        ):
            rv.append([ogb, SKOS.narrower, ogc])

        return rv


# class Harmonization(GraphRepo):
#     def __init__(self):
#         super().__init__()
#
#     def add(self, concept_scheme: ConceptScheme):
#         me_copy = self.copy()
#         for triple in concept_scheme.g:
#             me_copy.g.add(triple)
#         return me_copy
#
#     def connect(self, concept_1, concept_2, property_=SKOS.relatedMatch):
#         if concept_1 is None or concept_2 is None:
#             raise ValueError("'empty' concept(s) supplied")
#         allowed = {
#             SKOS.closeMatch,
#             SKOS.exactMatch,
#             SKOS.narrowMatch,
#             SKOS.relatedMatch,
#         }
#         if property_ not in allowed:
#             raise ValueError(f"`property_` must be in {allowed}")
#         me_copy = self.copy()
#         me_copy.g.add(
#             (
#                 self.local_id_for_concept(concept_1),
#                 property_,
#                 self.local_id_for_concept(concept_2),
#             )
#         )
#         return me_copy
#
#     def narrowmatch_bridge(self, concept_1, concept_2):
#         c1 = self.local_id_for_concept(concept_1).n3()
#         c2 = self.local_id_for_concept(concept_2).n3()
#         qres = self.g.query(
#             f"""
#         SELECT *
#         WHERE {{
#          {c1} skos:narrower*/(skos:narrowMatch|skos:exactMatch)/skos:narrower* {c2} .
#         }}
#         """,
#             initNs={"skos": SKOS},
#         )
#         return len(qres) != 0

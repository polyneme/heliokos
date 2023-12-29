import json
from collections import defaultdict
from datetime import datetime
from itertools import permutations
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

from bson import ObjectId
from pymongo import MongoClient, UpdateOne
from rdflib import Graph, URIRef, XSD, Literal, Dataset, OWL
from rdflib.namespace import SKOS, RDFS, RDF, Namespace
from toolz import merge, merge_with, dissoc

from heliokos.infra.config import MONGO_HOST, MONGO_USER, MONGO_PASSWORD, MONGO_TLS

RDFA_CORE_INITIAL_CONTEXT = json.loads(
    Path(__file__).parent.joinpath("static/rdfa11.json").read_text()
)

HK_CONTEXT = {
    "@context": {k: v for k, v in RDFA_CORE_INITIAL_CONTEXT["@context"].items()}
}
HK_CONTEXT["@context"] = merge(
    HK_CONTEXT["@context"],
    {
        "@base": "https://heliokos.example/",
        "helior": "https://n2t.net/ark:57802/p03295/",
        "openalex": "https://openalex.org/",
    },
)


CONTEXT_BASE = HK_CONTEXT["@context"]["@base"]


def core_context_prefix_map():
    return {k: v for k, v in HK_CONTEXT["@context"].items()}


def with_core_context(d):
    return merge(d, HK_CONTEXT)


def with_oid_id(d):
    return merge(d, {"@id": str(ObjectId())})


class ValidationError(Exception):
    pass


class HKGraph(Graph):
    """rdflib.Graph with particular prefix-to-namespace mappings."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for prefix, uri in core_context_prefix_map().items():
            if not prefix.startswith("@"):
                self.bind(prefix, Namespace(uri))
            elif prefix == "@base":
                self.bind("_", Namespace(uri))


hkgraph_namespace_manager = HKGraph().namespace_manager


def curiefy(thing):
    if isinstance(thing, URIRef):
        return thing.n3(hkgraph_namespace_manager)
    else:
        return thing


def expand_curie(s: str):
    if s.startswith("<"):  # not a CURIE. a full URI.
        return URIRef(s[1:-1])  # strip leading '<' and trailing '>'
    else:
        return hkgraph_namespace_manager.expand_curie(s)


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

_collection.create_index({"s": 1, "edge.p": 1, "edge.o": 1, "g": 1})
_collection.create_index({"edge.p": 1, "edge.o": 1, "s": 1, "g": 1})
_collection.create_index({"edge.o": 1, "edge.p": 1, "s": 1, "g": 1})

_collection.create_index({"g": 1, "s": 1, "edge.p": 1, "edge.o": 1})
_collection.create_index({"g": 1, "edge.p": 1, "edge.o": 1, "s": 1})
_collection.create_index({"g": 1, "edge.o": 1, "edge.p": 1, "s": 1})


CONCEPT_RELATIONS_ALLOWED = {SKOS.narrower, SKOS.related}


class Concept:
    """
    Represent a skos:Concept.

    Support setting skos:narrower only, with skos:broader inferrable.
    Rationale: https://www.w3.org/TR/vocab-data-cube/#schemes-hierarchy
    """

    def __init__(self, label=None, uri=None):
        self.g = HKGraph()

        if uri is None:
            uri = f"{CONTEXT_BASE}{ObjectId()}"
        self.uri = URIRef(uri)
        self.g.add((self.uri, RDF.type, SKOS.Concept))

        if label is not None:
            self.g.add((self.uri, SKOS.prefLabel, Literal(label)))

    @property
    def pref_label(self):
        return self.g.value(self.uri, SKOS.prefLabel)

    @property
    def curie(self):
        return curiefy(self.uri)

    def __repr__(self):
        return json.dumps(
            {"uri": self.uri, "curie": self.curie, "pref_label": self.pref_label}
        )


class ConceptScheme:
    def __init__(self, label=None, uri=None):
        self.g = HKGraph()

        if uri is None:
            uri = f"{CONTEXT_BASE}{ObjectId()}"
        self.uri = URIRef(uri)
        self.g.add((self.uri, RDF.type, SKOS.ConceptScheme))

        self.label = Literal(str(self.uri))
        if label is not None:
            self.g.add((self.uri, SKOS.prefLabel, Literal(label)))
            self.label = Literal(label)

    @classmethod
    def from_graph(cls, g: Graph, error_msg_extra=""):
        uri = g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
        if uri is None:
            error_msg_extra = f" {error_msg_extra}" if error_msg_extra else ""
            raise ValueError(
                "no ConceptScheme found in supplied graph" + error_msg_extra
            )
        label = g.value(subject=uri, predicate=SKOS.prefLabel)
        cs = cls(label=label, uri=uri)
        cs.g = g
        return cs

    @classmethod
    def from_file(cls, filepath: Path):
        file_graph = Graph()
        file_graph.parse(filepath)
        return cls.from_graph(file_graph, error_msg_extra=f"from filepath {filepath}")

    @classmethod
    def from_repo(cls, repo, uri: URIRef):
        g = repo.load_graph(uri)
        return cls.from_graph(g, error_msg_extra=f"{uri} from repo")

    @property
    def curie(self):
        return curiefy(self.uri)

    def add(self, concept: Concept):
        for triple in concept.g:
            self.g.add(triple)
        return self

    def set_as_top_concept(self, concept: Concept):
        self.g.add((self.uri, SKOS.hasTopConcept, concept.uri))

    def connect(
        self, concept_1: Concept, concept_2: Concept, property_: URIRef = SKOS.related
    ):
        if property_ not in CONCEPT_RELATIONS_ALLOWED:
            raise ValueError(f"`property_` must be in {CONCEPT_RELATIONS_ALLOWED}")
        self.g.add((concept_1.uri, property_, concept_2.uri))
        return self

    def find_concept_by_pref_label(self, pref_label):
        return self.g.value(predicate=SKOS.prefLabel, object=Literal(pref_label))

    #
    # def to_file(self):
    #     me_id = self.g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
    #     Path(".scheme").mkdir(exist_ok=True)
    #     self.g.serialize(f".scheme/{me_id.split('/')[-1]}.ttl")

    @property
    def concept_uris(self):
        return set(self.g.subjects(predicate=RDF.type, object=SKOS.Concept))

    @property
    def concepts(self):
        rv = []
        for uri, pref_label in self.g.query(
            f"""
                SELECT ?c ?clabel
                WHERE {{
                ?c a skos:Concept .
                ?c skos:prefLabel ?clabel .
                }}""",
            initNs={"skos": SKOS},
        ):
            rv.append(Concept(label=pref_label, uri=uri))
        return rv

    @property
    def relations(self) -> list[list[URIRef]]:
        rv = []
        relation_values = " ".join([f"<{r}>" for r in CONCEPT_RELATIONS_ALLOWED])
        query = f"""
        SELECT ?s ?relation ?o
            WHERE {{
                VALUES ?relation {{ {relation_values} }}
                ?s ?relation ?o .
            }}"""
        for s_id, relation, o_id in self.g.query(query):
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
        for oga, ogb, ogc in self.g.query(
            query_narrow_transitive_with_related, initNs={"skos": SKOS}
        ):
            rv.append([ogb, SKOS.narrower, ogc])

        return rv


SSSOM = Namespace("https://w3id.org/sssom/")


def new_uri():
    return URIRef(f"{CONTEXT_BASE}{ObjectId()}")


class Harmonization:
    """A sssom:MappingSet from subjects in a tagging scheme to objects in a retrieval scheme."""

    def __init__(self, label=None, uri=None):
        self.g = HKGraph()

        if uri is None:
            uri = new_uri()
        self.uri = URIRef(uri)
        self.uri_mappings = new_uri()
        self.retrieval_scheme, self.tagging_scheme = None, None

        self.g.add((self.uri, RDF.type, SSSOM.MappingSet))
        self.g.add((self.uri, SSSOM.mappings, self.uri_mappings))
        self.g.add((self.uri_mappings, RDF.type, RDF.Bag))

        if label is not None:
            self.g.add((self.uri, SKOS.prefLabel, Literal(label)))

    def set_retrieval_scheme(self, concept_scheme: ConceptScheme):
        self.retrieval_scheme = concept_scheme
        for triple in self.retrieval_scheme.g:
            self.g.add(triple)
        return self

    def set_tagging_scheme(self, concept_scheme: ConceptScheme):
        self.tagging_scheme = concept_scheme
        for triple in self.tagging_scheme.g:
            self.g.add(triple)
        return self

    def add_mapping(
        self, subject_id=None, predicate_id=SKOS.relatedMatch, object_id=None
    ):
        if subject_id is None or object_id is None:
            raise ValueError("both `subject_id` and `object_id` are required")
        allowed = {
            SKOS.closeMatch,
            SKOS.exactMatch,
            SKOS.narrowMatch,
            SKOS.relatedMatch,
        }
        if predicate_id not in allowed:
            raise ValueError(f"`predicate_id` must be in {allowed}")
        if subject_id not in self.tagging_scheme.concept_uris:
            raise ValueError(
                f"subject {subject_id} not in tagging scheme {self.tagging_scheme.label}."
            )
        if object_id not in self.retrieval_scheme.concept_uris:
            raise ValueError(
                f"object {object_id} not in retrieval scheme {self.retrieval_scheme.label}."
            )
        uri_m = new_uri()
        for triple in [
            (uri_m, RDF.type, SSSOM.Mapping),
            (uri_m, RDFS.member, self.uri_mappings),
            (uri_m, OWL.annotatedSource, subject_id),
            (uri_m, OWL.annotatedProperty, predicate_id),
            (uri_m, OWL.annotatedTarget, object_id),
        ]:
            self.g.add(triple)
        return self

    def narrowmatch_bridge(self, concept_1_uri, concept_2_uri):
        c1, c2 = concept_1_uri.n3(), concept_2_uri.n3()
        qres = self.g.query(
            f"""
        SELECT *
        WHERE {{
         VALUES ?property {{ skos:narrowMatch skos:exactMatch }}
         ?mapping a sssom:Mapping .
         ?mapping owl:annotatedProperty ?property .
         ?mapping owl:annotatedSource ?mapping_subject .
         {c1} skos:narrower* ?mapping_subject .
         ?mapping owl:annotatedTarget ?mapping_object .
         ?mapping_object skos:narrower* {c2} .
        }}
        """,
            initNs={"skos": SKOS, "owl": OWL, "sssom": SSSOM},
        )
        return len(qres) != 0


class GraphRepo:
    """An interface to a persisted set of named graphs."""

    def __init__(self, name=None, graph_uris: list[URIRef] | None = None):
        self.ds = Dataset()  # In-memory representation
        self.coll = get_mongodb()[
            "nodes" if name is None else name
        ]  # Persisted information
        self.graph_uris = [curiefy(uri) for uri in graph_uris] if graph_uris else []
        self.filter = {"g": {"$in": self.graph_uris}} if self.graph_uris else {}

    def find(self, pre_filter, predicate_objects=None, sort=None, limit=0):
        filter_ = pre_filter
        predicate_objects = predicate_objects or []
        for p, o in predicate_objects:
            if p is not None and o is not None:
                filter_["edge"]["$all"].append({"$elemMatch": {"p": p, "o": o}})
            elif p is not None:
                filter_["edge"]["$all"].append({"$elemMatch": {"p": p}})
            elif o is not None:
                filter_["edge"]["$all"].append({"$elemMatch": {"o": o}})
        return self.coll.find(filter_, sort=sort, limit=limit)

    @property
    def filter_concepts(self):
        return merge(
            self.filter,
            {
                "edge": {
                    "$all": [{"$elemMatch": {"p": "rdf:type", "o": "skos:Concept"}}]
                }
            },
        )

    def find_concepts(self, predicate_objects=None, sort=None, limit=0):
        return self.find(self.filter_concepts, predicate_objects, sort, limit)

    def find_one_concept(self, predicate_objects=None):
        rv = list(self.find_concepts(predicate_objects, limit=1))
        return rv[0] if rv else None

    def find_one_concept_by_id(self, subject_id=None):
        return self.coll.find_one(merge(self.filter_concepts, {"s": subject_id}))

    @property
    def filter_concept_schemes(self):
        return merge(
            self.filter,
            {
                "edge": {
                    "$all": [
                        {"$elemMatch": {"p": "rdf:type", "o": "skos:ConceptScheme"}}
                    ]
                }
            },
        )

    def find_concept_schemes(self, predicate_objects=None, sort=None, limit=0):
        return self.find(self.filter_concept_schemes, predicate_objects, sort, limit)

    def find_one_concept_scheme(self, predicate_objects=None):
        rv = list(self.find_concept_schemes(predicate_objects, limit=1))
        return rv[0] if rv else None

    def find_one_concept_scheme_by_id(self, subject_id=None):
        return self.coll.find_one(merge(self.filter_concept_schemes, {"s": subject_id}))

    def upsert_one(self, graph_id, subject_id, predicate_objects):
        filter_ = {"g": graph_id, "s": subject_id}
        now = datetime_now()
        update = {
            "$set": {"g": graph_id, "s": subject_id, "env.lu": now},
            "$addToSet": {
                "edge": {"$each": [{"p": p, "o": o} for p, o in predicate_objects]}
            },
        }
        return self.coll.update_one(filter_, update, upsert=True)

    def set_edge(self, g, s, p, o):
        return self.upsert_one(g, s, [(p, o)])

    def upsert_one_concept(
        self, predicate_objects=None, subject_id=None, graph_id=None
    ):
        graph_id = graph_id or "_:public"
        subject_id = subject_id or curiefy(new_uri())
        predicate_objects = predicate_objects or []
        return self.upsert_one(
            graph_id, subject_id, predicate_objects + [("rdf:type", "skos:Concept")]
        )

    def upsert_one_concept_scheme(
        self, predicate_objects=None, subject_id=None, graph_id=None
    ):
        graph_id = graph_id or curiefy(new_uri())
        subject_id = subject_id or curiefy(new_uri())
        predicate_objects = predicate_objects or []
        return self.upsert_one(
            graph_id,
            subject_id,
            predicate_objects + [("rdf:type", "skos:ConceptScheme")],
        )

    @staticmethod
    def add_docs_to_graph(docs, g: Graph = None):
        if g is None:
            g = HKGraph()
        for doc in docs:
            s_id = expand_curie(doc["s"])
            for s_edge in doc["edge"]:
                s_edge_p = expand_curie(s_edge["p"])
                s_edge_o = (
                    Literal(s_edge["o"])
                    if s_edge_p in has_literal_range
                    else expand_curie(s_edge["o"])
                )
                g.add(
                    (
                        s_id,
                        s_edge_p,
                        s_edge_o,
                    )
                )
        return g

    def load_graph(self, graph_id):
        if not isinstance(graph_id, URIRef):
            raise TypeError("`graph_id` must be a uri (`URIRef`)")
        g = self.add_docs_to_graph(
            self.coll.find({"g": curiefy(graph_id)}, ["s", "edge"])
        )
        return self.ds.graph(graph_id) + g

    def load_concept(self, uri):
        if not isinstance(uri, URIRef):
            raise TypeError("`uri` must be a `URIRef`")
        doc = self.find_one_concept_by_id(curiefy(uri))
        if doc is None:
            raise ValueError(f"concept {uri} not found in repo")
        concept = Concept(label=concept_pref_label(doc), uri=expand_curie(doc["s"]))
        concept.g = self.add_docs_to_graph([doc], concept.g)
        return concept

    def load_concept_scheme(self, uri) -> ConceptScheme:
        g = self.load_graph(uri)
        return ConceptScheme()

    def upsert_graph(self, g: Graph, graph_id):
        if not isinstance(graph_id, URIRef):
            raise ValueError("`graph_id` must be a uri (`URIRef`)")
        s_edge = defaultdict(list)
        for triple in g:
            s, p, o = [curiefy(term) for term in triple]
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
        g_id = curiefy(graph_id)
        updates = [
            {
                "filter": {"g": g_id, "s": s},
                "update": {"$set": {"g": g_id, "s": s, "edge": edge, "env.lu": now}},
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


def doc2concept(doc):
    return Concept(label=concept_pref_label(doc), uri=doc["s"])


def concept_pref_label(doc):
    for edge in doc["edge"]:
        if edge["p"] == "skos:prefLabel":
            return edge["o"]
    return None


def doc2scheme(doc):
    return ConceptScheme(label=concept_scheme_label(doc), uri=doc["s"])


def concept_scheme_label(doc):
    for edge in doc["edge"]:
        if edge["p"] == "dcterms:title":
            return edge["o"]
        elif edge["p"] == "skos:prefLabel":
            return edge["o"]
        elif edge["p"] == "rdfs:label":
            return edge["o"]
    return None

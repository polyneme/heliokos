import json
import uuid
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import SKOS, RDFS, RDF, OWL
from toolz import merge

RDFA_CORE_INITIAL_CONTEXT = json.loads(
    Path(__file__).parent.joinpath("static/rdfa11.json").read_text()
)


def core_context_prefix_map():
    return {k: v for k, v in RDFA_CORE_INITIAL_CONTEXT["@context"].items()}


def with_core_context(d):
    return merge(d, RDFA_CORE_INITIAL_CONTEXT)


def with_uuid_id(d):
    return merge(d, {"@id": str(uuid.uuid4())})


class ValidationError(Exception):
    pass


class RDFGraphDocument:
    """
    A rdflib graph fragment where there is one and only one "root" subject.
    """

    @classmethod
    def from_file(cls, filepath: str):
        if not filepath.startswith("/"):
            # relative to `helioweb` project root dir
            filepath = Path(__file__).parent.parent.parent.parent.joinpath(filepath)
        g = Graph()
        g.parse(filepath)
        return cls(data=json.loads(g.serialize(format="json-ld"))[0])

    def __init__(self, data=None):
        self.g = Graph()
        init_data = {} if data is None else data
        if len(init_data) == 0:
            init_data = with_uuid_id(with_core_context({"@type": "rdfs:Resource"}))
        if "@context" not in init_data:
            init_data = with_core_context(init_data)
        if "@id" not in init_data:
            init_data = with_uuid_id(init_data)
        if "@type" not in init_data:
            init_data["@type"] = "rdfs:Resource"
        self.g.parse(
            data=init_data,
            format="json-ld",
        )
        self.id = next(self.g.subjects())
        self.check()

    @property
    def id_suffix(self):
        return str(self.id).split("/")[-1]

    @property
    def label(self):
        rv = self.g.value(self.id, SKOS.prefLabel)
        if rv is None:
            rv = self.g.value(self.id, RDFS.label)
        if rv is None:
            rv = f"@id={self.id}"
        return rv

    def update(self, doc):
        self.g.parse(data=doc, format="json-ld")
        self.check()

    def check(self):
        if len(list(self.g.subjects(unique=True))) != 1:
            raise ValidationError(f"document '{self.label}' has more than one subject")

    def __repr__(self):
        return json.dumps(json.loads(self.g.serialize(format="json-ld"))[0], indent=2)


class RDFGraphRepo:
    """
    A general rdf graph.

    IDEA: make this class abstract,
        with rdflib implementation for
        - testing (in-memory),
        - prototyping (file-backed), and
        - production (oxigraph-backed).

    """

    @classmethod
    def from_file(cls, filepath: str):
        if not filepath.startswith("/"):
            # relative to `helioweb` project root dir
            filepath = Path(__file__).parent.parent.parent.parent.joinpath(filepath)
        g = Graph()
        g.parse(filepath)
        return cls(g=g)

    def __init__(self, g=None):
        self.g = Graph() if g is None else g

    def copy(self):
        g_copy = Graph()
        for triple in self.g:
            g_copy.add(triple)
        repo_copy = self.__class__()
        repo_copy.g = g_copy
        return repo_copy

    def add_graph_document(self, doc: RDFGraphDocument):
        for triple in doc.g:
            self.g.add(triple)

    def add_graph_from_file(self, path: Path):
        self.g.parse(path)

    def graph_document_by_id(self, id_):
        doc_g = Graph()
        for t in self.g.triples((URIRef(id_), None, None)):
            doc_g.add(t)
        return json.loads(doc_g.serialize(format="json-ld"))[0]

    def graph_neighborhood_for_concept(self, concept):
        outbound = [t for t in self.g.triples((concept.id, None, None))]
        inbound = [t for t in self.g.triples((None, None, concept.id))]
        return inbound, outbound

    def local_id_for_concept(self, concept):
        id_ = concept.id
        if (id_, RDF.type, SKOS.Concept) in self.g:
            return id_
        else:
            subject = self.g.value(subject=None, predicate=OWL.sameAs, object=id_)
            return (
                subject
                if (subject is not None and (subject, RDF.type, SKOS.Concept) in self.g)
                else None
            )

    def __repr__(self):
        return self.g.serialize(format="ttl")

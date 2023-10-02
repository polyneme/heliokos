import json
import uuid
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import SKOS, RDFS
from toolz import merge

RDFA_CORE_INITIAL_CONTEXT = json.loads(
    Path(__file__).parent.joinpath("rdfa11.json").read_text()
)


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

    def __init__(self, init_data=None):
        self.g = Graph()
        data = {} if init_data is None else init_data
        if len(data) == 0:
            data = with_uuid_id(with_core_context({"@type": "rdfs:Resource"}))
        if "@context" not in data:
            data = with_core_context(data)
        if "@id" not in data:
            data = with_uuid_id(data)
        if "@type" not in data:
            data["@type"] = "rdfs:Resource"
        self.g.parse(
            data=data,
            format="json-ld",
        )
        self.id = next(self.g.subjects())
        self.check()

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
    def __init__(self):
        self.g = Graph()

    def add(self, doc: RDFGraphDocument):
        for triple in doc.g:
            self.g.add(triple)

    def add_from_file(self, path: Path):
        self.g.parse(path)

    def get_document_by_id(self, id_):
        doc_g = Graph()
        for t in self.g.triples((URIRef(id_), None, None)):
            doc_g.add(t)
        return json.loads(doc_g.serialize(format="json-ld"))[0]

    def neighborhood_for(self, concept):
        outbound = [t for t in self.g.triples((concept.id, None, None))]
        inbound = [t for t in self.g.triples((None, None, concept.id))]
        return inbound, outbound

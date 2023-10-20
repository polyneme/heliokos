from jinja2 import Environment, PackageLoader, select_autoescape
from rdflib import SKOS

from heliokos.domain.core import ConceptScheme

jinja_env = Environment(
    loader=PackageLoader("heliokos.ui", "templates"),
    autoescape=select_autoescape(),
)

REGION_NS = "https://n2t.net/ark:57802/p03295/"


def page_for(concept, inbound, outbound):
    concept_link = concept.id.removeprefix(REGION_NS)
    inbound_local = [
        (s.removeprefix(REGION_NS), p, o.removeprefix(REGION_NS)) for s, p, o in inbound
    ]
    outbound_local = [
        (s.removeprefix(REGION_NS), p, o.removeprefix(REGION_NS))
        for s, p, o in outbound
    ]
    concept_preflabel = core_repo.g.value(concept.id, SKOS.prefLabel)
    return jinja_env.get_template("concept_neighborhood.html").render(
        concept_preflabel=concept_preflabel,
        concept_link=concept_link,
        inbound=inbound_local,
        outbound=outbound_local,
    )

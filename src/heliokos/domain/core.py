from pathlib import Path

from heliokos.infra.core import (
    GraphRepo,
    core_context_prefix_map,
    ConceptScheme,
    expand_curie,
    HKGraph,
)

repo = GraphRepo()


print("loading HelioRegion ConceptScheme...")
try:
    cs_helioregion = ConceptScheme.from_repo(
        repo, expand_curie("helior:HeliophysicsRegionBasedTaxonomy")
    )
except ValueError:
    print("Not found. Upserting HelioRegion ConceptScheme...")
    cs_helioregion = ConceptScheme.from_file(
        Path(__file__).parent.parent.joinpath("domain/helioregion.ttl")
    )
    repo.upsert_graph(cs_helioregion.g, cs_helioregion.uri)
    print("Upserting HelioRegion concepts to public graph...")
    g_concepts = HKGraph()
    for concept in cs_helioregion.concepts:
        g_concepts += concept.g
    repo.upsert_graph(g_concepts, expand_curie("_:public"))


print("loading OpenAlex ConceptScheme...")
try:
    cs_openalex = ConceptScheme.from_repo(repo, expand_curie("_:OpenAlex"))
except ValueError:
    print("Not found. Upserting OpenAlex ConceptScheme...")
    cs_openalex = ConceptScheme.from_file(
        Path(__file__).parent.parent.joinpath("infra/static/openalex.ttl")
    )
    repo.upsert_graph(cs_openalex.g, cs_openalex.uri)
    print("Upserting OpenAlex concepts to public graph...")
    g_concepts = HKGraph()
    for concept in cs_openalex.concepts:
        g_concepts += concept.g
    repo.upsert_graph(g_concepts, expand_curie("_:public"))


def get_full_repo():
    return GraphRepo()


def get_concept_repo():
    return GraphRepo(graph_uris=[expand_curie("_:public")])


class Corpus:
    pass


class GroundTruth:
    pass


class SearchIndex:
    pass


# cs_helioregion = ConceptScheme.from_file(
#     Path(__file__).parent.joinpath("helioregion.ttl")
# )
# cs_openalex = ConceptScheme.from_file(
#     Path(__file__).parent.parent.joinpath("infra/static/openalex.ttl")
# )


def expand_prefix(prefix):
    core_map = core_context_prefix_map()
    if prefix in core_map:
        return core_map[prefix]
    elif prefix == "helior":
        return "https://n2t.net/ark:57802/p03295/"
    elif prefix == "openalex":
        return "https://openalex.org/"
    else:
        return prefix

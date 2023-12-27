from pathlib import Path

from heliokos.infra.core import (
    GraphRepo,
    core_context_prefix_map,
    ConceptScheme,
    expand_curie,
)

repo = GraphRepo()


print("loading HelioRegion ConceptScheme...")
cs_helioregion = ConceptScheme.from_repo(
    repo, expand_curie("helior:HeliophysicsRegionBasedTaxonomy")
)
if len(cs_helioregion.g) == 0:
    print("Not found. Upserting HelioRegion ConceptScheme...")
    cs_helioregion = ConceptScheme.from_file(
        Path(__file__).parent.parent.joinpath("domain/helioregion.ttl")
    )
    repo.upsert_graph(cs_helioregion.g, cs_helioregion.uri)

print("loading OpenAlex ConceptScheme...")
cs_openalex = ConceptScheme.from_repo(repo, expand_curie("_:OpenAlex"))
if len(cs_openalex.g) == 0:
    print("Not found. Upserting OpenAlex ConceptScheme...")
    cs_openalex = ConceptScheme.from_file(
        Path(__file__).parent.parent.joinpath("infra/static/openalex.ttl")
    )
    repo.upsert_graph(cs_openalex.g, cs_openalex.uri)


def get_repo():
    return repo


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

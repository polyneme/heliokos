from pathlib import Path

from heliokos.infra.core import (
    GraphRepo,
    core_context_prefix_map,
    ConceptScheme,
    CONTEXT_BASE,
)


class Corpus:
    pass


class GroundTruth:
    pass


class SearchIndex:
    pass


concept_repo = ConceptRepo(uri=f"{CONTEXT_BASE}concepts")

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

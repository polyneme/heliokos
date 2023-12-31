"""
Functional tests.
"""
from pathlib import Path

from rdflib import SKOS

from heliokos.domain.core import (
    Corpus,
    GroundTruth,
    SearchIndex,
)
from heliokos.infra.core import Concept, ConceptScheme, Harmonization


def test_harmonizing_two_concept_schemes():
    """
    Given concept scheme cs1 and concept scheme cs2, you can make a harmonization.
    With a harmonization, you can connect concepts across schemes using specific edges.

    Example:
        1. Concept scheme cs1 is simply Physics--narrower-->Magnetic field.
        2. Concept scheme cs2 is simply Solar wind--narrower-->Heliosphere.
        3. We harmonize the two by adding a Magnetic field--narrowMatch-->Solar wind relation.
        4. We confirm that Heliosphere is transitively narrower than Physics in our harmonization.
    """
    c1 = Concept("Physics")
    c2 = Concept("Magnetic field")
    cs1 = ConceptScheme().add(c1).add(c2).connect(c1, c2, SKOS.narrower)

    assert cs1.relations == [[c1.uri, SKOS.narrower, c2.uri]]

    c3 = Concept("Solar wind")
    c4 = Concept("Heliosphere")
    cs2 = ConceptScheme().add(c3).add(c4).connect(c3, c4, SKOS.narrower)

    assert cs2.relations == [[c3.uri, SKOS.narrower, c4.uri]]

    h = Harmonization(tagging_scheme=cs1, retrieval_scheme=cs2).add_mapping(
        c2.uri, SKOS.narrowMatch, c3.uri
    )

    assert h.narrowmatch_bridge(c1.uri, c4.uri)


def test_harmonize_helioregion_concept_scheme_with_openalex_concept_scheme():
    """
    Here, we ensure we can
        1. load the `helioregion` concept scheme
        2. load the `openalex` concept scheme
        3. Harmonize the two, incompletely, via one connection.
        4. Confirm a transitive entailment.
    """
    # TODO also consider SPASE schema for harmonization workflow
    cs_helioregion = ConceptScheme.from_file(
        Path(__file__).parent.parent.joinpath("src/heliokos/domain/helioregion.ttl")
    )
    cs_openalex = ConceptScheme.from_file(
        Path(__file__).parent.parent.joinpath("src/heliokos/infra/static/openalex.ttl")
    )
    h = Harmonization(
        tagging_scheme=cs_openalex, retrieval_scheme=cs_helioregion
    ).add_mapping(
        cs_openalex.find_concept_by_pref_label("Atmospheric physics"),
        SKOS.exactMatch,
        cs_helioregion.find_concept_by_pref_label("Atmospheric Physics"),
    )
    assert h.narrowmatch_bridge(
        cs_openalex.find_concept_by_pref_label("Physics"),
        cs_helioregion.find_concept_by_pref_label("Polar Vortex"),
    )


def test_usability_of_harmonization_workflow():
    """
    Support for usability study for "concept scheme harmonization" workflow.

    Three tasks, each of which is intended to take a usability-study participant no more than ten minutes to complete.

    The tasks, to be done via web browser (HTML over HTTP) UI:

        1. Create a simple concept scheme, with one top concept and two additional concepts, both of which
            are directly narrower than the top concept. Export this concept scheme to a Turtle file.

        2. Load the helioregion concept scheme, and create a harmonization between it (as tagging scheme)
            and your simple concept scheme (as retrieval scheme).
            You may add a new top concept to your simple scheme, remove any existing concepts, etc.

        3. Export your harmonization both with and without entailments, as two separate Turtle files.

    Rather than via browser automation (e.g. Selenium), this testing is done by
        1. Issuing HTTP requests,
        2. Navigating hypertext responses, and
        3. Repeating as necessary to complete the task.
    """
    # TODO: once a UI is available, encode steps here to (a) confirm that each task's flow is supported,
    #  and (2) to signal regression from support for this particular assumed success flow.
    assert False


def test_load_corpus_and_make_search_index():
    """
    1. Load the `ads_playground` corpus, which is a subset of ADS records that are known to appear in
        OpenAlex and thus may be tagged with concepts from the `openalex` concept scheme.

    2. Load a search index for the corpus that uses the `openalex` concept scheme.

    3. Load a harmonization of 'uat' as retrieval scheme to `openalex` as tagging scheme.

    3. Perform a search that demonstrates an increase in recall relative to a search on an index made only
        from `openalex`.

    4. Perform a search that demonstrates an increase in precision relative to a search on an index made only
        from `openalex`.
    """
    ads_playground = Corpus.from_builtin("ads_playground")
    cs_helioregion = ConceptScheme.from_file("helioregion.ttl")
    cs_openalex = ConceptScheme.from_file("openalex.ttl")
    harmonization = (
        Harmonization()
        .add(cs_helioregion)
        .add(cs_openalex)
        .connect(
            cs_helioregion.find_one("Atmospheric Physics"),
            cs_openalex.find_one("Atmospheric physics"),
            SKOS.exactMatch,
        )
    )
    test_query = "some cool query"
    gt = GroundTruth.from_references_of(
        Corpus[:10]
    )  # first 10 items are review articles relevant to `test_query`
    si_openalex_only = (
        SearchIndex(over=ads_playground).from_concept_scheme(cs_openalex).build()
    )
    si_harmonized = (
        SearchIndex(over=ads_playground).from_harmonization(harmonization).build()
    )
    assert si_harmonized.r100(test_query, ground_truth=gt) > si_openalex_only.r100(
        test_query, ground_truth=gt
    )
    assert si_harmonized.p10(test_query, ground_truth=gt) > si_openalex_only.p10(
        test_query, ground_truth=gt
    )


def test_usability_of_search_evaluation_workflow():
    """
    Support for usability study for "search evaluation" workflow.

    Three tasks, each of which is intended to take a usability-study participant no more than ten minutes to complete.

    The tasks, to be done via web browser (HTML over HTTP) UI:

        1. Load the helioregion and openalex concept schemes, and create a harmonization for them. You need
            only do this with the goal of supporting a particular search query you have in mind. You might make
            only one connection, or you may make several. Your harmonization will be incomplete, and that's fine.

        2. Create a search-index comparator, by
            (a) choosing the ads_playground corpus as the common corpus,
            (b) choosing the openalex concept scheme as the baseline semantic artifact, and
            (c) choosing your harmonization as the semantic artifact under test.

            Build the comparator.

        3.  Enter your query as the common query for a search-relevance comparison,
            and choose the default ground-truth strategy.
            Request a R100 analysis. Does your harmonization improve recall?
            Request a P10 analysis. Does your harmonization improve precision?

    Rather than via browser automation (e.g. Selenium), this testing is done by
        1. Issuing HTTP requests,
        2. Navigating hypertext responses, and
        3. Repeating as necessary to complete the task.
    """
    # TODO: once a UI is available, encode steps here to (a) confirm that each task's flow is supported,
    #  and (2) to signal regression from support for this particular assumed success flow.
    assert False

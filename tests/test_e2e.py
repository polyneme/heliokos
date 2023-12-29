"""
Testing of HTTP requests + responses.
e2e -> "end-to-end".
"""
import secrets
from functools import cache

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from rdflib import URIRef

from heliokos.domain.core import get_concept_repo
from heliokos.infra.core import curiefy, GraphRepo, expand_curie
from heliokos.ui.main import app, get_full_repo


client = TestClient(app)

repo = get_full_repo()
concept_repo = get_concept_repo()


@cache
def make_soup(html_doc):
    return BeautifulSoup(html_doc, "html.parser")


def test_read_home():
    soup = make_soup(client.get("/").text)
    assert soup.select("h1")[0].text == "HelioKOS"
    assert len(soup.select("[data-hk-list='schemes'] li")) >= 2


def test_read_concepts():
    soup = make_soup(client.get("/concept").text)
    assert soup.select("h1")[0].text == "Concepts"
    assert len(soup.select("[data-hk-list='concepts'] li")) >= 2


def test_search_concepts():
    data = client.post(
        "/concepts-search",
        headers={"Hk-Combo-Box": "true"},
        data={"searched_concept": "Space"},
    ).json()
    assert len(data) >= 2
    soup = make_soup(
        client.post("/concepts-search", data={"searched_concept": "Space"}).text
    )
    assert len(soup.select("hk-combo-box datalist option")) >= 2


def test_create_concept():
    label = secrets.token_urlsafe()
    repo.coll.delete_many({"edge.o": label})
    soup = make_soup(client.post("/concept", data={"pref_label": label}).text)
    repo.coll.delete_many({"edge.o": label})
    assert soup.select("[data-hk-list='concepts'] li")[0].text == label


def test_read_concept():
    concept_curie = "helior:SpacePhysics"
    soup = make_soup(client.get(f"/concept/{concept_curie}").text)
    assert len(soup.select("main dl dt")) >= 2


def test_read_concept_schemes():
    soup = make_soup(client.get(f"/conceptscheme").text)
    assert len(soup.select("[data-hk-list='schemes'] li")) >= 2


def test_create_concept_scheme():
    soup = make_soup(client.post(f"/conceptscheme").text)
    repo.coll.find_one_and_delete(
        {"edge.p": "rdf:type", "edge.o": "skos:ConceptScheme"}, sort=[("_id", -1)]
    )
    assert soup.select("h1")[0].text == "Scheme"


def test_read_concept_scheme():
    soup = make_soup(client.post(f"/conceptscheme").text)
    uri = URIRef(soup.select("main dl dd")[0].text)
    soup = make_soup(client.get(f"/conceptscheme/{curiefy(uri)}").text)
    assert soup.select("h1")[0].text == "Scheme"


def test_add_concept_to_concept_scheme():
    client.post(f"/conceptscheme")
    scheme_curie = repo.coll.find_one(
        {"edge.p": "rdf:type", "edge.o": "skos:ConceptScheme"}, sort=[("_id", -1)]
    )["s"]
    concept_curie = concept_repo.find_one_concept()["s"]
    soup = make_soup(
        client.post(
            f"/conceptscheme/{scheme_curie}/concept",
            data={"searched_concept_id": concept_curie},
        ).text
    )
    repo.coll.find_one_and_delete(
        {"edge.p": "rdf:type", "edge.o": "skos:ConceptScheme"}, sort=[("_id", -1)]
    )
    assert any(
        concept_curie in str(dd)
        for dd in soup.select('[data-hk-list="scheme-concepts"] dd')
    )


def test_add_relation_to_concept_scheme():
    client.post(f"/conceptscheme")
    scheme_curie = repo.coll.find_one(
        {"edge.p": "rdf:type", "edge.o": "skos:ConceptScheme"}, sort=[("_id", -1)]
    )["s"]
    concept_curies = [d["s"] for d in concept_repo.find_concepts(limit=2)]
    for cc in concept_curies:
        client.post(
            f"/conceptscheme/{scheme_curie}/concept",
            data={"searched_concept_id": cc},
        )
    soup = make_soup(
        client.post(
            f"/conceptscheme/{scheme_curie}/relation",
            data={
                "subject_concept_id": concept_curies[0],
                "object_concept_id": concept_curies[1],
                "relation": "narrower",
            },
        ).text
    )
    repo.coll.delete_many({"g": scheme_curie})
    assert any(
        (
            (concept_curies[0] in str(li))
            and (concept_curies[1] in str(li))
            and ("narrower" in str(li))
        )
        for li in soup.select('[data-hk-section="scheme-relationships"] li')
    )

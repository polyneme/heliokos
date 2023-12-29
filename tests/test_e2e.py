"""
Testing of HTTP requests + responses.
e2e -> "end-to-end".
"""
from functools import cache

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from rdflib import URIRef

from heliokos.domain.core import get_concept_repo
from heliokos.infra.core import curiefy
from heliokos.ui.main import app


client = TestClient(app)


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
    concept_repo = get_concept_repo()
    label = "Freedom of Screech"
    concept_repo.coll.delete_many(
        {"edge": {"$elemMatch": {"p": "skos:prefLabel", "o": label}}}
    )
    soup = make_soup(client.post("/concept", data={"pref_label": label}).text)
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
    assert soup.select("h1")[0].text == "Scheme"


def test_read_concept_scheme():
    soup = make_soup(client.post(f"/conceptscheme").text)
    uri = URIRef(soup.select("main dl dd")[0].text)
    soup = make_soup(client.get(f"/conceptscheme/{curiefy(uri)}").text)
    assert soup.select("h1")[0].text == "Scheme"


def test_add_concept_to_concept_scheme():
    scheme_curie = curiefy(
        URIRef(
            make_soup(client.post(f"/conceptscheme").text).select("main dl dd")[0].text
        )
    )
    concept_curie = get_concept_repo().find_one_concept()["s"]
    soup = make_soup(
        client.post(
            f"/conceptscheme/{scheme_curie}/concept",
            data={"searched_concept_id": concept_curie},
        ).text
    )
    assert any(
        concept_curie in str(dd)
        for dd in soup.select('[data-hk-list="scheme-concepts"] dd')
    )


def test_add_relation_to_concept_scheme():
    raise NotImplementedError

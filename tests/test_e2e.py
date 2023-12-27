"""
Testing of HTTP requests + responses.
e2e -> "end-to-end".
"""
from functools import cache

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

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
    raise NotImplementedError


def test_search_concepts():
    raise NotImplementedError


def test_create_concept():
    raise NotImplementedError


def test_read_concept():
    raise NotImplementedError


def test_read_concept_schemes():
    raise NotImplementedError


def test_create_concept_scheme():
    raise NotImplementedError


def test_read_concept_scheme():
    raise NotImplementedError


def test_add_concept_to_concept_scheme():
    raise NotImplementedError


def test_add_relation_to_concept_scheme():
    raise NotImplementedError

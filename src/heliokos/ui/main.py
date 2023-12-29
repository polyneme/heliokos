"""
Intent: a hypermedia application,
i.e. sticking to HTTP-over-HTML as much as possible,
with the aid of the <a href="https://htmx.org/">htmx</a> Javascript library.

backend:
- FastAPI app returning HTML responses
- Jinja2 to render Representation of Resource
- File-backed RDFLib graphs (for now)
"""
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Header, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from rdflib import SKOS
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from heliokos.domain.core import get_full_repo, get_concept_repo
from heliokos.infra.core import (
    Concept,
    GraphRepo,
    ConceptScheme,
    concept_scheme_label,
    concept_pref_label,
    doc2concept,
    doc2scheme,
    expand_curie,
    curiefy,
    CONCEPT_RELATIONS_ALLOWED,
    CONTEXT_BASE,
)
from heliokos.ui.core import raise404_if_none

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.joinpath("static")),
    name="static",
)
templates = Jinja2Templates(directory=Path(__file__).parent.joinpath("templates"))
templates.env.globals.update({"GLOBALS_today_year": str(date.today().year)})


@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request, full_repo: GraphRepo = Depends(get_full_repo)):
    schemes = [
        {"id": d["s"], "label": concept_scheme_label(d)}
        for d in full_repo.find_concept_schemes()
    ]
    concepts = [
        {"id": d["s"], "label": concept_pref_label(d)}
        for d in full_repo.find_concepts(sort=[("env.lu", -1)], limit=25)
    ]
    return templates.TemplateResponse(
        "home.html", {"request": request, "schemes": schemes, "concepts": concepts}
    )


@app.get("/concept", response_class=HTMLResponse)
async def read_concepts(
    request: Request, concept_repo: GraphRepo = Depends(get_concept_repo)
):
    concepts = [
        {"id": d["s"], "label": concept_pref_label(d)}
        for d in concept_repo.find_concepts(sort=[("env.lu", -1)], limit=25)
    ]
    return templates.TemplateResponse(
        "concepts.html", {"request": request, "concepts": concepts}
    )


@lru_cache
def concept_pref_labels():
    """Call concept_pref_labels.cache_clear() when concepts are added/modified/removed."""
    # TODO restrict to dedicated "global" concepts graph (or "user" concepts graph plus "global" concepts graph)
    repo = get_concept_repo()
    return {doc["s"]: concept_pref_label(doc) for doc in repo.find_concepts()}


@app.post("/concepts-search")
@app.get("/concepts-search")
async def search_concepts(
    request: Request,
    searched_concept: Annotated[str | None, Form()] = None,
    hk_combo_box: Annotated[str | None, Header()] = None,
):
    if searched_concept:
        results = [
            {"pl": pl, "id_": curie}
            for curie, pl in concept_pref_labels().items()
            if searched_concept in pl
        ]
    else:
        results = []
    if hk_combo_box:
        return [
            {"id": r["id_"], "value": r["pl"]}
            for r in results[:50]  # return at most 50 results at a time
        ]
    else:
        return templates.TemplateResponse(
            "concepts-search.html", {"request": request, "results": results}
        )


@app.post("/concept", response_class=HTMLResponse)
async def create_concept(
    pref_label: Annotated[str, Form()],
    request: Request,
    concept_repo: GraphRepo = Depends(get_concept_repo),
):
    doc = concept_repo.find_one_concept([("skos:prefLabel", pref_label)])
    if doc is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'concept with preferred label "{pref_label}" <a href="/concept/{doc["s"]}">already exists</a>.',
        )
    concept_repo.upsert_one_concept([("skos:prefLabel", pref_label)])
    concept_pref_labels.cache_clear()
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concepts"),
    )


@app.get("/concept/{id_}", response_class=HTMLResponse)
async def read_concept(
    request: Request, id_: str, repo: GraphRepo = Depends(get_full_repo)
):
    doc = raise404_if_none(
        repo.find_one_concept_by_id(id_), detail=f"concept {id_} not found"
    )
    concept = doc2concept(doc)
    return templates.TemplateResponse(
        "concept.html", {"request": request, "concept": concept}
    )


@app.get("/conceptscheme", response_class=HTMLResponse)
async def read_concept_schemes(
    request: Request, repo: GraphRepo = Depends(get_full_repo)
):
    schemes = [doc2scheme(d) for d in repo.find_concept_schemes()]
    return templates.TemplateResponse(
        "schemes.html", {"request": request, "schemes": schemes}
    )


@app.post("/conceptscheme", response_class=HTMLResponse)
async def create_concept_scheme(
    request: Request, repo: GraphRepo = Depends(get_full_repo)
):
    scheme = ConceptScheme()
    repo.upsert_graph(scheme.g, scheme.uri)
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concept_scheme", id_=curiefy(scheme.uri)),
    )


@app.get("/conceptscheme/{id_}", response_class=HTMLResponse)
async def read_concept_scheme(
    id_: str,
    request: Request,
    repo: GraphRepo = Depends(get_full_repo),
    concept_repo: GraphRepo = Depends(get_concept_repo),
):
    raise404_if_none(repo.find_one_concept_scheme_by_id(id_))
    scheme = ConceptScheme.from_repo(repo, expand_curie(id_))
    concepts_exist = len(list(concept_repo.find_concepts(limit=2))) == 2
    scheme_concepts_by_id = {c.uri: c for c in scheme.concepts}
    relations = [
        [
            scheme_concepts_by_id[s],
            p,
            scheme_concepts_by_id[o],
        ]
        for s, p, o in scheme.relations
    ]
    deny_relations = [
        [
            scheme_concepts_by_id[s].uri,
            p.fragment,
            scheme_concepts_by_id[o].uri,
        ]
        for s, p, o in scheme.deny_relations
    ]
    return templates.TemplateResponse(
        "scheme.html",
        {
            "request": request,
            "scheme": scheme,
            "relations": relations,
            "deny_relations": deny_relations,
            "concepts_exist": concepts_exist,
        },
    )


@app.post("/conceptscheme/{id_}/concept", response_class=HTMLResponse)
async def add_concept_to_concept_scheme(
    id_: str,
    searched_concept_id: Annotated[str, Form()],
    request: Request,
    repo: GraphRepo = Depends(get_full_repo),
    concept_repo: GraphRepo = Depends(get_concept_repo),
):
    raise404_if_none(repo.find_one_concept_scheme_by_id(id_))
    concept = concept_repo.load_concept(expand_curie(searched_concept_id))
    repo.upsert_graph(concept.g, expand_curie(id_))
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concept_scheme", id_=id_),
    )


@app.post("/conceptscheme/{id_}/relation", response_class=HTMLResponse)
async def add_relation_to_concept_scheme(
    id_: str,
    subject_concept_id: Annotated[str, Form()],
    object_concept_id: Annotated[str, Form()],
    relation: Annotated[str, Form()],
    request: Request,
    repo: GraphRepo = Depends(get_full_repo),
):
    allowed_relations = {r.fragment for r in CONCEPT_RELATIONS_ALLOWED}
    try:
        getattr(SKOS, relation)
    except AttributeError:
        return Response(
            f"relation must be in SKOS vocabulary",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if relation not in allowed_relations:
        return Response(
            f"relation must be one of {allowed_relations}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    raise404_if_none(repo.find_one_concept_scheme_by_id(id_))
    scheme = ConceptScheme.from_repo(repo, expand_curie(id_))
    concepts = scheme.concepts
    try_concept_id = subject_concept_id
    try:
        subject_concept = next(c for c in concepts if c.curie == try_concept_id)
        try_concept_id = object_concept_id
        object_concept = next(c for c in concepts if c.curie == try_concept_id)
    except StopIteration:
        return Response(
            f"concept {try_concept_id} not found in scheme {id_}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    t_relation = getattr(SKOS, relation)
    if [subject_concept.uri, t_relation, object_concept.uri] in scheme.relations:
        return Response(
            f"relation already in scheme",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if [subject_concept.uri, t_relation, object_concept.uri] in scheme.deny_relations:
        return Response(
            f"relation disallowed due to current relations in scheme",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    scheme.connect(subject_concept, object_concept, getattr(SKOS, relation))
    repo.upsert_graph(scheme.g, scheme.uri)
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concept_scheme", id_=id_),
    )

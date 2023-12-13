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
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Header
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from rdflib import SKOS
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from heliokos.domain.core import (
    Concept,
    cs_helioregion,
    expand_prefix,
    ConceptScheme,
    RELATIONS_ALLOWED,
    cs_openalex,
)
from heliokos.infra.core import CONTEXT_BASE
from heliokos.ui.html import page_for

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.joinpath("static")),
    name="static",
)
templates = Jinja2Templates(directory=Path(__file__).parent.joinpath("templates"))
templates.env.globals.update({"GLOBALS_today_year": str(date.today().year)})


@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    schemes = []
    for filepath in Path(".scheme/").glob("*.ttl"):
        schemes.append(ConceptScheme.from_file(str(filepath)))
    concepts = []
    for filepath in Path(".concept/").glob("*.ttl"):
        concepts.append(Concept.from_file(str(filepath)))
    return templates.TemplateResponse(
        "home.html", {"request": request, "schemes": schemes, "concepts": concepts}
    )


@app.get("/concept", response_class=HTMLResponse)
async def read_concepts(request: Request):
    concepts = []
    for filepath in Path(".concept/").glob("*.ttl"):
        concepts.append(Concept.from_file(str(filepath)))
    return templates.TemplateResponse(
        "concepts.html", {"request": request, "concepts": concepts}
    )


@app.get("/concepts-search", response_class=HTMLResponse)
async def search_concepts(request: Request):
    return templates.TemplateResponse(
        "concepts-search.html", {"request": request, "results": []}
    )


concept_pref_labels = {
    str(pref_label): str(id_)
    for id_, pref_label in cs_openalex.g.query(
        "SELECT ?c ?clabel WHERE { ?c a skos:Concept . ?c skos:prefLabel ?clabel }",
        initNs={"skos": SKOS},
    )
}


@app.post("/concepts-search", response_class=HTMLResponse)
async def search_concepts(
    request: Request,
    search: Annotated[str, Form()],
    hx_request: Annotated[str | None, Header()] = None,
):
    if search:
        results = (
            [
                {"pl": pl, "id_": id_}
                for pl, id_ in concept_pref_labels.items()
                if search in pl
            ]
            if search
            else []
        )
    else:
        results = []
    if hx_request:
        return "".join(
            f"<tr><th scope='row'>{r['id_']}</th><td>{r['pl']}</td></tr>"
            for r in results[:50]  # return at most 50 results at a time
        )
    else:
        return templates.TemplateResponse(
            "concepts-search.html", {"request": request, "results": results}
        )


@app.post("/concept", response_class=HTMLResponse)
async def create_concept(pref_label: Annotated[str, Form()], request: Request):
    concept = Concept(pref_label)
    concept.to_file()
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concepts"),
    )


@app.get("/concept/{id_}", response_class=HTMLResponse)
async def read_concept(id_: str, request: Request):
    concept = Concept.from_file(f".concept/{id_}.ttl")
    return templates.TemplateResponse(
        "concept.html", {"request": request, "concept": concept}
    )


@app.get("/conceptscheme", response_class=HTMLResponse)
async def read_concept_schemes(request: Request):
    schemes = []
    for filepath in Path(".scheme/").glob("*.ttl"):
        schemes.append(ConceptScheme.from_file(str(filepath)))
    return templates.TemplateResponse(
        "schemes.html", {"request": request, "schemes": schemes}
    )


@app.post("/conceptscheme", response_class=HTMLResponse)
async def create_concept_scheme(request: Request):
    scheme = ConceptScheme()
    scheme.to_file()
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concept_scheme", id_=scheme.id_suffix),
    )


@app.get("/conceptscheme/{id_}", response_class=HTMLResponse)
async def read_concept_scheme(id_: str, request: Request):
    scheme = ConceptScheme.from_file(f".scheme/{id_}.ttl")
    concepts = []
    for filepath in Path(".concept/").glob("*.ttl"):
        concepts.append(Concept.from_file(str(filepath)))
    scheme_concepts_by_id = {c.id: c for c in scheme.concepts}
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
            scheme_concepts_by_id[s].id_suffix,
            p.fragment,
            scheme_concepts_by_id[o].id_suffix,
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
            "concepts": concepts,
        },
    )


@app.post("/conceptscheme/{id_}/concept", response_class=HTMLResponse)
async def add_concept_to_concept_scheme(
    id_: str, selected_concept: Annotated[str, Form()], request: Request
):
    scheme = ConceptScheme.from_file(f".scheme/{id_}.ttl")
    concept = Concept.from_file(f".concept/{selected_concept}.ttl")
    scheme.add(concept).to_file()
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concept_scheme", id_=scheme.id.split("/")[-1]),
    )


@app.post("/conceptscheme/{id_}/relation", response_class=HTMLResponse)
async def add_relation_to_concept_scheme(
    id_: str,
    subject_concept_id: Annotated[str, Form()],
    object_concept_id: Annotated[str, Form()],
    relation: Annotated[str, Form()],
    request: Request,
):
    allowed_relations = {r.fragment for r in RELATIONS_ALLOWED}
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
    concepts = []
    for filepath in Path(".concept/").glob("*.ttl"):
        concepts.append(Concept.from_file(str(filepath)))
    scheme = ConceptScheme.from_file(f".scheme/{id_}.ttl")
    try_concept_id = subject_concept_id
    try:
        subject_concept = next(
            c
            for c in concepts
            if str(getattr(c, "id")) == CONTEXT_BASE + try_concept_id
        )
        try_concept_id = object_concept_id
        object_concept = next(
            c
            for c in concepts
            if str(getattr(c, "id")) == CONTEXT_BASE + try_concept_id
        )
    except StopIteration:
        return Response(
            f"concept {try_concept_id} not found",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    t_relation = getattr(SKOS, relation)
    if [subject_concept.id, t_relation, object_concept.id] in scheme.relations:
        return Response(
            f"relation already in scheme",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if [subject_concept.id, t_relation, object_concept.id] in scheme.deny_relations:
        return Response(
            f"relation disallowed due to current relations in scheme",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    scheme.connect(subject_concept, object_concept, getattr(SKOS, relation)).to_file()
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concept_scheme", id_=scheme.id.split("/")[-1]),
    )


@app.get("/resources/{id_}")
async def read_resource(id_: str, req: Request):
    print(id_)
    if ":" in id_:
        prefix, id_ = id_.split(":", maxsplit=1)
        id_ = expand_prefix(prefix) + id_

    concept = Concept(cs_helioregion.graph_document_by_id(id_))
    inbound, outbound = cs_helioregion.graph_neighborhood_for_concept(concept)
    if len(outbound) == 0:
        return HTMLResponse(f"{id_} not found", status_code=status.HTTP_404_NOT_FOUND)
    return HTMLResponse(
        content=page_for(concept=concept, inbound=inbound, outbound=outbound),
    )

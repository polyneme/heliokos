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

from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from heliokos.domain.core import Concept, cs_helioregion, expand_prefix, ConceptScheme
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
    return templates.TemplateResponse(
        "home.html", {"request": request, "schemes": schemes}
    )


@app.post("/concept", response_class=HTMLResponse)
async def create_concept(pref_label: Annotated[str, Form()], request: Request):
    concept = Concept(pref_label)
    concept.to_file()
    return RedirectResponse(
        status_code=status.HTTP_303_SEE_OTHER,
        url=request.url_for("read_concept", id_=concept.id_suffix),
    )


@app.get("/concept/{id_}", response_class=HTMLResponse)
async def read_concept(id_: str, request: Request):
    concept = Concept.from_file(f".concept/{id_}.ttl")
    return templates.TemplateResponse(
        "concept.html", {"request": request, "concept": concept}
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
    return templates.TemplateResponse(
        "scheme.html", {"request": request, "scheme": scheme, "concepts": concepts}
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

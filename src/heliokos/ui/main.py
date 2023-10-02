"""

- one HTTP Route, returning HTML Representation of Resource

infra:
- FastAPI app returning HTML responses
- Jinja2 to render Representation of Resource
"""

from fastapi import FastAPI
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse, HTMLResponse

from heliokos.domain.core import regions_repo, Concept
from heliokos.ui.html import page_for

app = FastAPI()


@app.get("/", include_in_schema=False)
def read_root(req: Request):
    return RedirectResponse(req.url_for("read_resource", id="home"))


@app.get("/resources/{id_}")
def read_resource(id_: str, req: Request):
    concept = Concept(
        {"@id": id_, "@context": {"@base": "https://n2t.net/ark:57802/p03295/"}}
    )
    print(concept)
    inbound, outbound = regions_repo.neighborhood_for(concept)
    if len(outbound) == 0:
        return HTMLResponse(f"{id_} not found", status_code=status.HTTP_404_NOT_FOUND)
    return HTMLResponse(
        content=page_for(concept=concept, inbound=inbound, outbound=outbound),
    )

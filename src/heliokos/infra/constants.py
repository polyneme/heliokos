import json
from pathlib import Path

RDFA_CORE_INITIAL_CONTEXT = json.loads(
    Path(__file__).parent.joinpath("rdfa11.json").read_text()
)

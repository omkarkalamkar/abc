import json
import os

INTERFACE = "https://schema.skao.int/ska-mid-cbf-initsysparam/1.0"
TELMODEL_SOURCE = os.getenv("TELMODEL_SOURCE")
ARRAY_LAYOUT_PATH = os.getenv("TELMODEL_PATH")


def get_load_dish_vcc_json(
    interface: str = INTERFACE,
    source: str = TELMODEL_SOURCE,
    path: str = ARRAY_LAYOUT_PATH,
    file_name: str | None = None,
):
    """Creates load dish vcc configuration json."""
    if file_name:
        directory = os.path.dirname(path)
        path = os.path.join(directory, file_name)

    vcc_json: dict = {
        "interface": interface,
        "tm_data_sources": [source],
        "tm_data_filepath": path,
    }
    return json.dumps(vcc_json)

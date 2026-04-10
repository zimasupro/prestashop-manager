import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as ET
from nicegui import app
from settings import MULTILANG_FIELDS


def _creds():
    url = app.storage.user.get("presta_url", "").rstrip("/")
    key = app.storage.user.get("presta_api_key", "")
    if not url or not key:
        raise RuntimeError("PrestaShop credentials not configured. Go to /setup.")
    return url, HTTPBasicAuth(key, "")


def _get(endpoint, params=None):
    if params is None:
        params = {}
    url, auth = _creds()
    response = requests.get(
        f"{url}/{endpoint}",
        auth=auth,
        params={"output_format": "JSON", "display": "full", **params},
    )
    response.raise_for_status()
    return response.json()


def _get_xml(endpoint):
    url, auth = _creds()
    response = requests.get(f"{url}/{endpoint}", auth=auth)
    response.raise_for_status()
    return response.text


def _patch(endpoint, xml_body: str):
    url, auth = _creds()
    response = requests.patch(
        f"{url}/{endpoint}",
        auth=auth,
        headers={"Content-Type": "text/xml"},
        data=xml_body.encode("utf-8"),
    )
    response.raise_for_status()
    return response.text


def _post(endpoint, xml_body: str):
    url, auth = _creds()
    response = requests.post(
        f"{url}/{endpoint}",
        auth=auth,
        headers={"Content-Type": "text/xml"},
        data=xml_body.encode("utf-8"),
    )
    response.raise_for_status()
    return response.text

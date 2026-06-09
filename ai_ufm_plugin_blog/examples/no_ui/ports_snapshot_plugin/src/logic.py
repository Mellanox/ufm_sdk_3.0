import os
from typing import Any, Dict, Iterable
from urllib.parse import urljoin

import requests


SOURCE_SCRIPT = "scripts/ufm_ports/load_ports.py"
API_PATH = "resources/ports"
QUERY_PARAMS = [
    "system",
    "active",
    "show_disabled"
]


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def _ufm_base_url() -> str:
    protocol = os.environ.get("UFM_PROTOCOL", "https")
    host = os.environ.get("UFM_HOST", "127.0.0.1")
    prefix = os.environ.get("UFM_REST_PREFIX", "/ufmRest")
    return f"{protocol}://{host}{prefix.strip()}/"


def _auth_kwargs() -> Dict[str, Any]:
    token = os.environ.get("UFM_ACCESS_TOKEN")
    if token:
        return {"headers": {"Authorization": f"Bearer {token}"}}
    username = os.environ.get("UFM_USERNAME")
    password = os.environ.get("UFM_PASSWORD")
    if username and password:
        return {"auth": (username, password)}
    return {}


def _coerce_bool(value: str | None, default: bool | None = None) -> str | None:
    if value is None or value == "":
        if default is None:
            return None
        return "true" if default else "false"
    return "true" if str(value).lower() in ("1", "true", "yes", "on") else "false"


def _filtered_params(args: Dict[str, str]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    for name in QUERY_PARAMS:
        value = args.get(name)
        if name in ("active", "show_disabled"):
            value = _coerce_bool(value, True if name == "active" else False)
        if value not in (None, ""):
            params[name] = value
    return params


def _limited(items: Any, limit_value: str | None) -> Any:
    if not limit_value:
        return items
    try:
        limit = int(limit_value)
    except ValueError:
        return items
    if isinstance(items, list) and limit >= 0:
        return items[:limit]
    return items


def collect(args: Dict[str, str]) -> Dict[str, Any]:
    url = urljoin(_ufm_base_url(), API_PATH)
    params = _filtered_params(args)
    verify = _env_bool("UFM_VERIFY_TLS", False)
    timeout = float(os.environ.get("UFM_REQUEST_TIMEOUT", "30"))
    request_kwargs = _auth_kwargs()
    response = requests.get(url, params=params, verify=verify, timeout=timeout, **request_kwargs)
    response.raise_for_status()
    payload = _limited(response.json(), args.get("limit"))
    return {
        "plugin": "ports_snapshot",
        "source_script": SOURCE_SCRIPT,
        "api_path": API_PATH,
        "query": params,
        "items": payload,
    }


def _iter_items(payload: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
    elif isinstance(payload, dict):
        for key in ("items", "ports", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item


def summarize(collection: Dict[str, Any]) -> Dict[str, Any]:
    items = list(_iter_items(collection.get("items")))
    active = 0
    disabled = 0
    states: Dict[str, int] = {}
    for item in items:
        active_value = item.get("active")
        if active_value in (True, "true", "True", 1, "1"):
            active += 1
        state = str(item.get("state") or item.get("physical_state") or item.get("logical_state") or "unknown")
        states[state] = states.get(state, 0) + 1
        if item.get("enabled") in (False, "false", "False", 0, "0"):
            disabled += 1
    return {
        "plugin": collection["plugin"],
        "source_script": collection["source_script"],
        "api_path": collection["api_path"],
        "total_items": len(items),
        "active_items": active,
        "disabled_items": disabled,
        "states": states,
        "sample": items[:5],
    }

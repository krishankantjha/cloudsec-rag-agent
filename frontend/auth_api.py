import os
import time
from typing import Any, Dict

import requests

API_BASE_URL = os.getenv("CLOUDSEC_API_URL", "https://cloudsec-rag-agent.onrender.com").rstrip("/")


def _post_with_retry(path: str, payload: Dict[str, Any], timeout: int = 30) -> requests.Response:
    # Handle brief backend startup/warm-up windows so first click doesn't fail.
    retry_delays = [0.35, 0.75, 1.25]
    last_error: Exception | None = None

    for attempt, delay in enumerate(retry_delays):
        try:
            return requests.post(
                f"{API_BASE_URL}{path}",
                json=payload,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            last_error = exc
            if attempt == len(retry_delays) - 1:
                break
            time.sleep(delay)

    raise last_error if last_error is not None else RuntimeError("Request failed without an error.")


def signup_user(email: str, password: str) -> Dict[str, Any]:
    response = _post_with_retry(
        "/signup",
        {"email": email, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def login_user(email: str, password: str) -> Dict[str, Any]:
    response = _post_with_retry(
        "/login",
        {"email": email, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def ask_agent(
    query: str,
    attachments: list[dict],
    token: str,
    timeout: int = 180,
    history: list[dict] | None = None,
) -> Dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/ask",
        json={"query": query, "attachments": attachments, "history": history or []},
        headers={"Authorization": f"Bearer {token}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()

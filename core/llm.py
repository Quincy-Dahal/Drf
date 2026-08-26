"""
core/llm.py

Thin client for the local Ollama server. 

Exposes:
    chat(messages, ...)            - multi-turn call, takes a list of
                                      {"role": ..., "content": ...} dicts
    ask(prompt, system=None, ...)  - single-turn convenience wrapper
    health()                       - checks server reachability + model
                                      availability, never raises

All failures raise a single LLMError with an actionable message, so callers
(views) can catch one exception type and return a clean 503 instead of
leaking a raw requests traceback to website visitors.
"""

import requests
from django.conf import settings


class LLMError(Exception):
    """Raised when the Ollama server can't be reached or returns an error."""
    pass


def _base_url():
    return getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")


def _model():
    return getattr(settings, "OLLAMA_MODEL", "qwen3:4b")


def _timeout():
    return getattr(settings, "OLLAMA_TIMEOUT", 120)


def _keep_alive():
    return getattr(settings, "OLLAMA_KEEP_ALIVE", "10m")


def chat(messages, model=None, think=False, timeout=None):
    """
    Multi-turn call to Ollama's /api/chat endpoint.

    messages: list of dicts, e.g. [{"role": "user", "content": "Hi"}]
    Returns the assistant's reply text (str).
    Raises LLMError on any failure (connection, timeout, missing model,
    HTTP error, or an unexpected response shape).
    """
    url = f"{_base_url()}/api/chat"
    payload = {
        "model": model or _model(),
        "messages": messages,
        "stream": False,
        "think": think,
        "keep_alive": _keep_alive(),
    }
    call_timeout = timeout or _timeout()

    try:
        response = requests.post(url, json=payload, timeout=call_timeout)
    except requests.exceptions.ConnectionError as exc:
        raise LLMError(
            f"Cannot reach Ollama at {_base_url()}. Is the service running? "
            "(ollama serve on Linux/WSL; check the tray icon on Windows/macOS)"
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise LLMError(
            f"Ollama did not respond within {call_timeout}s. The model may "
            "still be loading, or the machine may be under memory pressure."
        ) from exc

    if response.status_code == 404:
        raise LLMError(
            f"Model '{model or _model()}' is not pulled. "
            f"Run: ollama pull {model or _model()}"
        )

    if not response.ok:
        raise LLMError(
            f"Ollama returned HTTP {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
        return data["message"]["content"]
    except (ValueError, KeyError) as exc:
        raise LLMError(
            f"Unexpected response shape from Ollama: {response.text[:200]}"
        ) from exc


def ask(prompt, system=None, model=None, think=False, timeout=None):
    """
    Single-turn convenience wrapper around chat().

    prompt: the user's message (str)
    system: optional system prompt (str)
    Returns the assistant's reply text (str).
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return chat(messages, model=model, think=think, timeout=timeout)


def health():
    """
    Checks whether the Ollama server is reachable and the configured model
    is pulled. Never raises - always returns a dict describing status.

    Returns:
        {
            "ok": bool,
            "server_reachable": bool,
            "model_pulled": bool,
            "detail": str,
        }
    """
    result = {
        "ok": False,
        "server_reachable": False,
        "model_pulled": False,
        "detail": "",
    }

    try:
        response = requests.get(f"{_base_url()}/api/tags", timeout=5)
    except requests.exceptions.RequestException as exc:
        result["detail"] = f"Cannot reach Ollama at {_base_url()}: {exc}"
        return result

    if not response.ok:
        result["detail"] = f"Ollama returned HTTP {response.status_code} from /api/tags"
        return result

    result["server_reachable"] = True

    try:
        models = [m["model"] for m in response.json().get("models", [])]
    except (ValueError, KeyError):
        result["detail"] = "Ollama responded, but /api/tags returned an unexpected shape."
        return result

    target = _model()
    if target in models:
        result["model_pulled"] = True
        result["ok"] = True
        result["detail"] = "ok"
    else:
        result["detail"] = (
            f"Server is up, but '{target}' is not pulled. "
            f"Available models: {models or '(none)'}. Run: ollama pull {target}"
        )

    return result
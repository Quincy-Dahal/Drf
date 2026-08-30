"""
core/llm.py

"""

import re

import requests
from django.conf import settings

from .knowledge import RUDRANTRA_KNOWLEDGE_BASE


class LLMError(Exception):
    """Raised when the Ollama server can't be reached or returns an error."""
    pass


_THINK_TAG_RE = re.compile(r"</?think>", re.IGNORECASE)


def _strip_thinking(text):
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[-1]
    text = _THINK_TAG_RE.sub("", text)
    return text.strip()

RUDRANTRA_SYSTEM_PROMPT = (
    "You are the support assistant for Rudrantra, an online store selling "
    "Rudraksha beads. Only discuss Rudrantra's products, Rudraksha types and "
    "their meanings, pricing, shipping, and returns. If asked about anything "
    "unrelated, politely decline and steer back to these topics. Keep "
    "answers brief and to the point. Base every answer only on the store "
    "information below. If something a customer asks isn't covered here, "
    "don't say you lack information or mention a knowledge base - just "
    "warmly let them know the team will help directly, using the contact "
    "details below.\n"
    + RUDRANTRA_KNOWLEDGE_BASE
)

DEFAULT_MAX_TOKENS = None


def _base_url():
    return getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")


def _model():
    return getattr(settings, "OLLAMA_MODEL", "qwen3:4b")


def _timeout():
    return getattr(settings, "OLLAMA_TIMEOUT", 120)


def _keep_alive():
    return getattr(settings, "OLLAMA_KEEP_ALIVE", "10m")


def chat(
    messages,
    model=None,
    think=False,
    timeout=None,
    max_tokens=DEFAULT_MAX_TOKENS,
    system=RUDRANTRA_SYSTEM_PROMPT,
):
    
    if system and (not messages or messages[0].get("role") != "system"):
        messages = [{"role": "system", "content": system}] + list(messages)

    url = f"{_base_url()}/api/chat"
    payload = {
        "model": model or _model(),
        "messages": messages,
        "stream": False,
        "think": think,
        "keep_alive": _keep_alive(),
    }
    if max_tokens is not None:
        payload["options"] = {"num_predict": max_tokens}

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
        content = data["message"]["content"]
    except (ValueError, KeyError) as exc:
        raise LLMError(
            f"Unexpected response shape from Ollama: {response.text[:200]}"
        ) from exc

    return _strip_thinking(content)


def ask(
    prompt,
    system=RUDRANTRA_SYSTEM_PROMPT,
    model=None,
    think=False,
    timeout=None,
    max_tokens=DEFAULT_MAX_TOKENS,
):

    messages = [{"role": "user", "content": prompt}]
    return chat(
        messages,
        model=model,
        think=think,
        timeout=timeout,
        max_tokens=max_tokens,
        system=system,
    )


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
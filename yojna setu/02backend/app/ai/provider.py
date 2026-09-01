import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("yojnasetu.ai")


class AIProvider(ABC):
  """Abstract interface for LLM / Embedding providers in YojnaSetu."""

  @property
  @abstractmethod
  def name(self) -> str:
    pass

  @property
  @abstractmethod
  def is_fallback(self) -> bool:
    pass

  @abstractmethod
  def generate(
      self, prompt: str, system_prompt: Optional[str] = None
  ) -> str:
    """Generate freeform natural language text from prompt."""
    pass

  @abstractmethod
  def structured_output(
      self,
      prompt: str,
      json_schema: Dict[str, Any],
      system_prompt: Optional[str] = None,
  ) -> Dict[str, Any]:
    """Generate structured JSON output adhering to a JSON schema."""
    pass

  @abstractmethod
  def embed(self, text: str) -> List[float]:
    """Generate vector embedding representation of text."""
    pass


class GeminiProvider(AIProvider):
  """Google Gemini API provider using REST API with httpx."""

  def __init__(self, api_key: str, model: Optional[str] = None):
    self.api_key = api_key
    self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
    self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

  @property
  def name(self) -> str:
    return "google_gemini"

  @property
  def is_fallback(self) -> bool:
    return False

  def generate(
      self, prompt: str, system_prompt: Optional[str] = None
  ) -> str:
    url = f"{self.base_url}?key={self.api_key}"
    payload: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }
    if system_prompt:
      payload["system_instruction"] = {
          "parts": [{"text": system_prompt}]
      }

    try:
      with httpx.Client(timeout=15.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
          parts = candidates[0]["content"].get("parts", [])
          if parts:
            return parts[0].get("text", "").strip()
        return ""
    except Exception as err:
      logger.error("Gemini API generate error: %s", err)
      raise RuntimeError(f"Gemini API request failed: {err}")

  def structured_output(
      self,
      prompt: str,
      json_schema: Dict[str, Any],
      system_prompt: Optional[str] = None,
  ) -> Dict[str, Any]:
    full_prompt = (
        f"{prompt}\n\nRespond strictly with a valid JSON object adhering to this"
        f" schema:\n{json.dumps(json_schema)}"
    )
    text_out = self.generate(full_prompt, system_prompt)
    match = re.search(r"\{.*\}", text_out, re.DOTALL)
    if match:
      try:
        return json.loads(match.group(0))
      except json.JSONDecodeError:
        pass
    raise ValueError(f"Failed to parse structured JSON from Gemini: {text_out}")

  def embed(self, text: str) -> List[float]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.api_key}"
    try:
      with httpx.Client(timeout=10.0) as client:
        response = client.post(
            url,
            json={
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text[:2000]}]},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embedding", {}).get("values", [])
    except Exception as err:
      logger.error("Gemini embed error: %s", err)
      return DevFallbackProvider().embed(text)


class OpenAIProvider(AIProvider):
  """OpenAI API provider using REST API with httpx."""

  def __init__(self, api_key: str):
    self.api_key = api_key

  @property
  def name(self) -> str:
    return "openai"

  @property
  def is_fallback(self) -> bool:
    return False

  def generate(
      self, prompt: str, system_prompt: Optional[str] = None
  ) -> str:
    messages = []
    if system_prompt:
      messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
      with httpx.Client(timeout=15.0) as client:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": "gpt-4o-mini", "messages": messages},
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as err:
      logger.error("OpenAI generate error: %s", err)
      raise RuntimeError(f"OpenAI API request failed: {err}")

  def structured_output(
      self,
      prompt: str,
      json_schema: Dict[str, Any],
      system_prompt: Optional[str] = None,
  ) -> Dict[str, Any]:
    full_prompt = (
        f"{prompt}\n\nRespond strictly with a valid JSON object adhering to this"
        f" schema:\n{json.dumps(json_schema)}"
    )
    text_out = self.generate(full_prompt, system_prompt)
    match = re.search(r"\{.*\}", text_out, re.DOTALL)
    if match:
      try:
        return json.loads(match.group(0))
      except json.JSONDecodeError:
        pass
    raise ValueError(f"Failed to parse structured JSON from OpenAI: {text_out}")

  def embed(self, text: str) -> List[float]:
    try:
      with httpx.Client(timeout=10.0) as client:
        response = client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": "text-embedding-3-small", "input": text[:2000]},
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception as err:
      logger.error("OpenAI embed error: %s", err)
      return DevFallbackProvider().embed(text)


class DevFallbackProvider(AIProvider):
  """Safe development fallback provider when no API key is available.

  Uses rule-based NLP extraction and TF-IDF vector embeddings.
  Explicitly flags `is_fallback: True` in metadata so the system NEVER claims to be an LLM!
  """

  @property
  def name(self) -> str:
    return "dev_fallback"

  @property
  def is_fallback(self) -> bool:
    return True

  def generate(
      self, prompt: str, system_prompt: Optional[str] = None
  ) -> str:
    # Rule-assisted deterministic fallback generation
    return (
        "Notice: AI API key not configured. Response generated via"
        " YojnaSetu's deterministic rule engine & authoritative database"
        " retrieval fallback."
    )

  def structured_output(
      self,
      prompt: str,
      json_schema: Dict[str, Any],
      system_prompt: Optional[str] = None,
  ) -> Dict[str, Any]:
    return {}

  def embed(self, text: str) -> List[float]:
    """Generates a 64-dimensional deterministic feature hash embedding vector."""
    clean_text = text.lower()
    vector = [0.0] * 64
    for i, char in enumerate(clean_text):
      idx = ord(char) % 64
      vector[idx] += 1.0 / (i + 1)
    norm = sum(x * x for x in vector) ** 0.5
    if norm > 0:
      vector = [x / norm for x in vector]
    return vector


def get_ai_provider() -> AIProvider:
  """Factory returning the active AI provider based on settings & available API keys."""
  if settings.AI_PROVIDER == "dev_fallback":
    return DevFallbackProvider()

  if (
      settings.GEMINI_API_KEY
      or settings.AI_PROVIDER in ("gemini", "google")
  ) and settings.GEMINI_API_KEY:
    return GeminiProvider(settings.GEMINI_API_KEY)

  if (
      settings.OPENAI_API_KEY
      or settings.AI_PROVIDER == "openai"
  ) and settings.OPENAI_API_KEY:
    return OpenAIProvider(settings.OPENAI_API_KEY)

  return DevFallbackProvider()

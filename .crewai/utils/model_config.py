"""Centralized model configuration with global rate limiting."""

import os
import threading
import time
from dataclasses import dataclass
from typing import Optional

import litellm
from crewai import LLM


@dataclass
class ModelConfig:
    """Configuration for a single model."""

    name: str  # Full model name
    rpm_limit: int  # Requests per minute limit
    context_window: int  # Max context tokens
    supports_function_calling: bool = True
    supports_parallel_tools: bool = True
    is_free_tier: bool = False  # True for :free variants


# Available models - crews select from this list
MODEL_REGISTRY = {
    # Mistral Devstral 2512 (high performance, good function calling) - DEFAULT
    "mistral-devstral-2512": ModelConfig(
        name="openrouter/mistralai/devstral-2512",  # openrouter/ prefix needed for LiteLLM
        rpm_limit=60,
        context_window=262144,  # 262.1K context window
    ),
    # Gemini 2.5 Flash Lite (fallback option)
    "gemini-flash-lite": ModelConfig(
        name="openrouter/google/gemini-2.5-flash-lite",
        rpm_limit=60,
        context_window=1000000,
    ),
    # Gemini 2.0 Flash (original)
    "gemini-flash": ModelConfig(
        name="openrouter/google/gemini-2.0-flash-001",
        rpm_limit=60,
        context_window=1000000,
    ),
    # Free tier variant (20 RPM limit)
    "gemini-flash-free": ModelConfig(
        name="openrouter/google/gemini-2.0-flash-001:free",
        rpm_limit=20,
        context_window=1000000,
        is_free_tier=True,
    ),
    # MiMo V2 (1M context, for overflow)
    "mimo-v2": ModelConfig(
        name="openrouter/xiaomi/mimo-v2",
        rpm_limit=60,
        context_window=1000000,
    ),
}

DEFAULT_MODEL_KEY = "mistral-devstral-2512"
FALLBACK_MODEL_KEY = "gemini-flash-lite"


class GlobalRateLimiter:
    """Thread-safe global rate limiter shared across all crews."""

    _instance: Optional["GlobalRateLimiter"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._request_times: list[float] = []
        self._rpm_limit = 60  # Will be set to most restrictive limit
        self._lock = threading.Lock()

    def set_limit(self, rpm: int):
        """Set global RPM limit (uses most restrictive across all models)."""
        with self._lock:
            self._rpm_limit = min(self._rpm_limit, rpm)

    def wait_if_needed(self):
        """Block if rate limit would be exceeded."""
        with self._lock:
            now = time.time()
            # Remove requests older than 60 seconds
            self._request_times = [t for t in self._request_times if now - t < 60]

            if len(self._request_times) >= self._rpm_limit:
                sleep_time = 60 - (now - self._request_times[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    now = time.time()
                    self._request_times = [t for t in self._request_times if now - t < 60]

            self._request_times.append(time.time())

    @property
    def current_limit(self) -> int:
        return self._rpm_limit


_rate_limiter = GlobalRateLimiter()


def get_rate_limiter() -> GlobalRateLimiter:
    return _rate_limiter


def get_llm(model_key: Optional[str] = None) -> LLM:
    """Get a configured LLM instance.

    Args:
        model_key: Key from MODEL_REGISTRY, or None to use default/env

    Returns:
        Configured CrewAI LLM instance
    """
    model_key = model_key or os.getenv("MODEL_KEY", DEFAULT_MODEL_KEY)

    if model_key not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(MODEL_REGISTRY.keys())}")

    config = MODEL_REGISTRY[model_key]
    get_rate_limiter().set_limit(config.rpm_limit)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY required")

    return LLM(
        model=config.name,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        timeout=120,  # 120 second timeout for slow responses
        num_retries=3,  # Retry transient failures
        extra_headers={
            "HTTP-Referer": "https://github.com/borealBytes/startup-blueprint",
            "X-Title": "Startup Blueprint CrewAI Review",
        },
    )


def get_model_config(model_key: Optional[str] = None) -> ModelConfig:
    """Get model configuration without creating LLM instance."""
    model_key = model_key or os.getenv("MODEL_KEY", DEFAULT_MODEL_KEY)
    config = MODEL_REGISTRY.get(model_key)
    if not config:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(MODEL_REGISTRY.keys())}")
    return config


def register_models():
    """Register all models with LiteLLM for function calling support."""
    for config in MODEL_REGISTRY.values():
        if config.supports_function_calling:
            litellm.register_model(
                {
                    config.name: {
                        "supports_function_calling": True,
                        "supports_parallel_function_calling": config.supports_parallel_tools,
                    }
                }
            )


# Backwards compatibility
def register_trinity_model():
    """Deprecated: Use register_models() instead."""
    register_models()


# Legacy exports for backwards compatibility
DEFAULT_MODEL = MODEL_REGISTRY[DEFAULT_MODEL_KEY].name
FALLBACK_MODEL = MODEL_REGISTRY[FALLBACK_MODEL_KEY].name

"""Model configuration utilities."""

import litellm

# Default model - Gemini Flash 2.0 is free and has reliable function calling
DEFAULT_MODEL = "openrouter/google/gemini-2.0-flash-exp:free"

# Fallback for large context (1M tokens)
FALLBACK_MODEL = "openrouter/google/gemini-2.0-flash-exp:free"


def register_models():
    """Register models with LiteLLM for function calling support.

    Some models support function calling but LiteLLM doesn't recognize them
    by default. This causes CrewAI to fall back to text-based ReAct pattern.

    Note: Gemini Flash 2.0 is already recognized by LiteLLM, but we register
    it explicitly to ensure consistent behavior.
    """
    # Gemini Flash 2.0 - Google's fast model with good function calling
    # LiteLLM should already know about this, but register to be safe
    litellm.register_model(
        {
            "openrouter/google/gemini-2.0-flash-exp:free": {
                "supports_function_calling": True,
                "supports_parallel_function_calling": True,
            }
        }
    )


# Backwards compatibility alias
def register_trinity_model():
    """Deprecated: Use register_models() instead."""
    register_models()

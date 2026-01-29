"""Model configuration utilities."""

import litellm


def register_trinity_model():
    """Register Trinity model with LiteLLM for function calling support.

    OpenRouter confirms Trinity supports `tools` and `supports_tool_choice`,
    but LiteLLM doesn't recognize it as function-calling capable by default.
    This causes CrewAI to fall back to text-based ReAct pattern instead of
    native function calling.

    See: https://openrouter.ai/arcee-ai/trinity-large-preview:free
    """
    litellm.register_model(
        {
            "openrouter/arcee-ai/trinity-large-preview:free": {
                "supports_function_calling": True,
                "supports_parallel_function_calling": True,
            }
        }
    )

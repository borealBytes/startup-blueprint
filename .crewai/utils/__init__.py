"""Utility modules for CrewAI configuration."""

from .model_config import DEFAULT_MODEL, FALLBACK_MODEL, register_models, register_trinity_model

__all__ = ["register_models", "register_trinity_model", "DEFAULT_MODEL", "FALLBACK_MODEL"]

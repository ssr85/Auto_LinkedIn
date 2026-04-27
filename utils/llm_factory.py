
import os
from typing import Optional, Any
from crewai import LLM
from utils.logger import log
from config import settings

def get_llm(model_name: str, temperature: float = 0.7, **kwargs) -> Any:
    """
    Factory function to return the appropriate CrewAI LLM instance 
    based on the model name and configured provider flags.
    
    Strictly enforces provider flags from settings and uses CrewAI's native 
    LLM class for better integration with CrewAI 1.11.0+.
    """
    # 0. Defensive cleanup: Remove ALL potential provider-specific keys from kwargs.
    # We enforce settings as the single source of truth for auth/base_url.
    colliding_keys = [
        "api_key", "openai_api_key", "anthropic_api_key", "openrouter_api_key",
        "base_url", "openai_api_base", "api_base", "anthropic_api_url"
    ]
    for key in colliding_keys:
        if key in kwargs:
            log.debug(f"Stripping '{key}' from kwargs to prevent collisions.")
            kwargs.pop(key)

    # 1. Route through OpenRouter if enabled (High Priority)
    if settings.use_openrouter:
        if not settings.openrouter_api_key:
            log.error("USE_OPENROUTER is true but OPENROUTER_API_KEY is missing")
            raise ValueError("OpenRouter API key required when USE_OPENROUTER=true")
            
        log.info(f"Routing '{model_name}' through OpenRouter")
        # For OpenRouter in CrewAI/LiteLLM, we prefix with 'openrouter/' 
        # to ensure it doesn't trigger native provider checks (like google/ or anthropic/)
        return LLM(
            model=f"openrouter/{model_name}" if not model_name.startswith("openrouter/") else model_name,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
            **kwargs
        )

    # 2. Route to Anthropic if enabled and model matches Claude
    if settings.use_anthropic and "claude" in model_name.lower():
        if not settings.anthropic_api_key:
            log.error("USE_ANTHROPIC is true but ANTHROPIC_API_KEY is missing")
            raise ValueError("Anthropic API key required when USE_ANTHROPIC=true")
            
        log.info(f"Using Anthropic model: {model_name}")
        return LLM(
            model=model_name,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
            **kwargs
        )
    
    # 3. Route to OpenAI if enabled
    if settings.use_openai:
        if not settings.openai_api_key:
            log.error("USE_OPENAI is true but OPENAI_API_KEY is missing")
            raise ValueError("OpenAI API key required when USE_OPENAI=true")
            
        log.info(f"Using OpenAI model: {model_name}")
        return LLM(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=temperature,
            **kwargs
        )

    # 4. Final Fallback/Error
    error_msg = f"No active provider found for model '{model_name}'. "
    error_msg += f"Check .env flags: USE_OPENAI={settings.use_openai}, USE_ANTHROPIC={settings.use_anthropic}, USE_OPENROUTER={settings.use_openrouter}"
    log.error(error_msg)
    raise ValueError(error_msg)

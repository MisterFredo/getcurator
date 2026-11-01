
import json
import logging
import os
import time
import uuid

from typing import Optional

from openai import OpenAI


logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_LLM_MODEL = "gpt-4o"

DEFAULT_SYSTEM_PROMPT = (
    "Tu es un assistant éditorial expert B2B."
)

LLM_PROFILES = {
    "legacy": "OPENAI_MODEL_LEGACY",
    "basic": "OPENAI_MODEL_BASIC",
    "smart": "OPENAI_MODEL_SMART",
    "production": "OPENAI_MODEL_PRODUCTION",
}

LLM_FALLBACK_MODELS = {
    "legacy": "gpt-4o",
    "basic": "gpt-4o",
    "smart": "gpt-4o",
    "production": "gpt-5.4",
}


# ============================================================
# MODEL RESOLUTION
# ============================================================

def resolve_llm_model(
    model: Optional[str] = None,
    profile: Optional[str] = None,
) -> str:

    if model:
        return model

    if not profile:
        return os.getenv(
            "OPENAI_MODEL_DEFAULT",
            DEFAULT_LLM_MODEL,
        )

    if profile not in LLM_PROFILES:
        raise ValueError(
            f"Unknown LLM profile: {profile}"
        )

    env_name = LLM_PROFILES[profile]

    return (
        os.getenv(env_name)
        or LLM_FALLBACK_MODELS[profile]
    )


# ============================================================
# GET LLM
# ============================================================

def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.2,
    profile: Optional[str] = None,
):

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None, "OPENAI_API_KEY manquant"

    try:
        resolved_model = resolve_llm_model(
            model=model,
            profile=profile,
        )

        client = OpenAI(
            api_key=api_key,
        )

        return {
            "client": client,
            "model": resolved_model,
            "temperature": temperature,
        }, None

    except Exception as error:
        return None, str(error)


# ============================================================
# API PARAMETERS
# ============================================================

def _supports_custom_temperature(
    model: str,
) -> bool:

    # Conservative compatibility rule:
    # reasoning-model families may not accept
    # arbitrary temperature values.
    #
    # Model-specific support must be verified
    # before enabling custom temperature.

    model_name = model.lower()

    if model_name.startswith((
        "gpt-5",
        "gpt-6",
        "o1",
        "o3",
        "o4",
    )):
        return False

    return True


def _build_completion_params(
    model: str,
    prompt: str,
    system_prompt: Optional[str],
    temperature: float,
    json_mode: bool,
) -> dict:

    params = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    system_prompt
                    or DEFAULT_SYSTEM_PROMPT
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    if _supports_custom_temperature(model):
        params["temperature"] = temperature

    if json_mode:
        params["response_format"] = {
            "type": "json_object",
        }

    return params


# ============================================================
# USAGE EXTRACTION
# ============================================================

def _extract_usage(
    completion,
) -> dict:

    usage = getattr(
        completion,
        "usage",
        None,
    )

    if usage is None:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "reasoning_output_tokens": 0,
        }

    input_tokens = (
        getattr(usage, "prompt_tokens", 0)
        or 0
    )

    output_tokens = (
        getattr(usage, "completion_tokens", 0)
        or 0
    )

    prompt_details = getattr(
        usage,
        "prompt_tokens_details",
        None,
    )

    completion_details = getattr(
        usage,
        "completion_tokens_details",
        None,
    )

    cached_tokens = (
        getattr(
            prompt_details,
            "cached_tokens",
            0,
        )
        or 0
    )

    reasoning_tokens = (
        getattr(
            completion_details,
            "reasoning_tokens",
            0,
        )
        or 0
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_tokens,
        "reasoning_output_tokens": reasoning_tokens,
    }


# ============================================================
# USAGE LOGGING
# ============================================================

def _log_llm_usage(
    *,
    request_id: str,
    operation: str,
    profile: str,
    model: str,
    duration_ms: int,
    status: str,
    usage: dict,
    error: Optional[str] = None,
):

    payload = {
        "event": "llm_usage",
        "request_id": request_id,
        "operation": operation,
        "profile": profile,
        "model": model,
        "duration_ms": duration_ms,
        "status": status,
        **usage,
    }

    if error:
        payload["error"] = error[:500]

    try:
        logger.warning(
            "LLM_USAGE %s",
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
        )
    except Exception:
        # Logging must never interrupt
        # the application workflow.
        pass


# ============================================================
# COMMON EXECUTION
# ============================================================

def _execute_llm(
    prompt: str,
    model: Optional[str],
    temperature: float,
    system_prompt: Optional[str],
    profile: Optional[str],
    operation: Optional[str],
    json_mode: bool,
) -> str:

    request_id = str(uuid.uuid4())

    started_at = time.perf_counter()

    resolved_model = model or "unresolved"

    usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "reasoning_output_tokens": 0,
    }

    try:
        cfg, error = get_llm(
            model=model,
            temperature=temperature,
            profile=profile,
        )

        if error:
            raise RuntimeError(error)

        resolved_model = cfg["model"]

        params = _build_completion_params(
            model=resolved_model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=cfg["temperature"],
            json_mode=json_mode,
        )

        completion = (
            cfg["client"]
            .chat
            .completions
            .create(**params)
        )

        usage = _extract_usage(
            completion
        )

        content = (
            completion
            .choices[0]
            .message
            .content
        )

        if not isinstance(content, str):
            content = ""

        status = (
            "success"
            if content
            else "empty"
        )

        duration_ms = int(
            (time.perf_counter() - started_at)
            * 1000
        )

        _log_llm_usage(
            request_id=request_id,
            operation=operation or "unknown",
            profile=profile or "default",
            model=resolved_model,
            duration_ms=duration_ms,
            status=status,
            usage=usage,
        )

        return content

    except Exception as error:

        duration_ms = int(
            (time.perf_counter() - started_at)
            * 1000
        )

        _log_llm_usage(
            request_id=request_id,
            operation=operation or "unknown",
            profile=profile or "default",
            model=resolved_model,
            duration_ms=duration_ms,
            status="error",
            usage=usage,
            error=str(error),
        )

        logger.exception(
            "LLM execution failed: "
            "operation=%s model=%s",
            operation or "unknown",
            resolved_model,
        )

        # Preserve legacy return contract.
        return ""


# ============================================================
# RUN LLM
# ============================================================

def run_llm(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    system_prompt: Optional[str] = None,
    profile: Optional[str] = None,
    operation: Optional[str] = None,
) -> str:

    return _execute_llm(
        prompt=prompt,
        model=model,
        temperature=temperature,
        system_prompt=system_prompt,
        profile=profile,
        operation=operation,
        json_mode=False,
    )


# ============================================================
# RUN LLM JSON
# ============================================================

def run_llm_json(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
    system_prompt: Optional[str] = None,
    profile: Optional[str] = None,
    operation: Optional[str] = None,
) -> str:

    return _execute_llm(
        prompt=prompt,
        model=model,
        temperature=temperature,
        system_prompt=system_prompt,
        profile=profile,
        operation=operation,
        json_mode=True,
    )

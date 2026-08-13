import os

from openai import (
    OpenAI,
)


DEFAULT_LLM_MODEL = "gpt-4o"

DEFAULT_SYSTEM_PROMPT = (
    "Tu es un assistant éditorial expert B2B."
)


# ============================================================
# GET LLM
# ============================================================

def get_llm(
    model: str = None,
    temperature: float = 0.2,
):

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:

        return (
            None,
            "OPENAI_API_KEY manquant",
        )

    try:

        client = OpenAI(
            api_key=api_key,
        )

    except Exception as e:

        return (
            None,
            str(e),
        )

    return {

        "client": client,

        "model":
            model
            or DEFAULT_LLM_MODEL,

        "temperature":
            temperature,

    }, None


# ============================================================
# RUN LLM
# ============================================================

def run_llm(
    prompt: str,
    model: str = None,
    temperature: float = 0.2,
    system_prompt: str = None,
) -> str:

    cfg, error = get_llm(
        model=model,
        temperature=temperature,
    )

    if error:

        return ""

    try:

        completion = (
            cfg["client"]
            .chat
            .completions
            .create(
                model=cfg["model"],

                messages=[
                    {
                        "role": "system",
                        "content":
                            system_prompt
                            or DEFAULT_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],

                temperature=
                    cfg["temperature"],
            )
        )

        message = (
            completion
            .choices[0]
            .message
        )

        content = (
            message.content
        )

        if isinstance(
            content,
            str,
        ):

            return content

        return ""

    except Exception:

        return ""

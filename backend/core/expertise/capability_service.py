import re

from utils.llm import (
    run_llm,
)

from api.expertise.models import (
    Expertise,
)

from core.expertise.prompts.executive_summary import (
    build_executive_summary_prompt,
)

from core.expertise.prompts.key_points import (
    build_key_points_prompt,
)

from core.expertise.prompts.structure import (
    build_structure_prompt,
)

from core.expertise.prompts.implications import (
    build_implications_prompt,
)

from core.expertise.capabilities import (
    CAPABILITY_EXECUTIVE_SUMMARY,
    CAPABILITY_KEY_POINTS,
    CAPABILITY_STRUCTURE,
    CAPABILITY_IMPLICATIONS,
)


# ============================================================
# CONFIGURATION
# ============================================================

CAPABILITY_TEMPERATURE = 0.0

IMPLICATIONS_MAX_ATTEMPTS = 3


# ============================================================
# FORBIDDEN IMPLICATION FORMULATIONS
# ============================================================

FORBIDDEN_IMPLICATION_PATTERNS = [

    r"\byou should\b",
    r"\byou must\b",
    r"\byou need\b",
    r"\byou have to\b",
    r"\byou can\b",

    r"\bconsider\b",
    r"\bfocus on\b",
    r"\bexplore\b",
    r"\bassess\b",
    r"\bevaluate\b",
    r"\badopt\b",
    r"\bintegrate\b",
    r"\binvest\b",
    r"\bprioriti[sz]e\b",
    r"\bleverage\b",

    r"\bneed for\b",
    r"\bneed to\b",
    r"\bpoint to assess\b",
    r"\bhighlights? (?:the )?need\b",
    r"\bsuggests? (?:a )?need\b",
    r"\brequires? you\b",
    r"\bopportunit(?:y|ies) to\b",

]


# ============================================================
# BUILD PROMPT
# ============================================================

def _build_prompt(
    capability: str,
    expertise: Expertise,
    context: dict | None = None,
) -> str:

    context = context or {}

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    if capability == CAPABILITY_EXECUTIVE_SUMMARY:

        return build_executive_summary_prompt(
            expertise=expertise,
            context=context,
        )

    # ========================================================
    # KEY POINTS
    # ========================================================

    if capability == CAPABILITY_KEY_POINTS:

        return build_key_points_prompt(
            expertise=expertise,
        )

    # ========================================================
    # STRUCTURE
    # ========================================================

    if capability == CAPABILITY_STRUCTURE:

        return build_structure_prompt(
            expertise=expertise,
        )

    # ========================================================
    # IMPLICATIONS
    # ========================================================

    if capability == CAPABILITY_IMPLICATIONS:

        return build_implications_prompt(
            expertise=expertise,
            context=context,
        )

    # ========================================================

    # UNKNOWN
    # ========================================================

    raise ValueError(
        f"Unknown capability: {capability}"
    )


# ============================================================
# VALIDATE IMPLICATIONS
# ============================================================

def _find_forbidden_implication_patterns(
    result: str,
) -> list[str]:

    if not result:

        return []

    return [

        pattern

        for pattern in (
            FORBIDDEN_IMPLICATION_PATTERNS
        )

        if re.search(
            pattern,
            result,
            flags=re.IGNORECASE,
        )

    ]


# ============================================================
# BUILD IMPLICATIONS CORRECTION PROMPT
# ============================================================

def _build_implications_correction_prompt(
    original_prompt: str,
    rejected_result: str,
    violations: list[str],
) -> str:

    violations_text = "\n".join(

        f"- {violation}"

        for violation in violations

    )

    return f"""
{original_prompt}


============================================================
CORRECTION REQUIRED
============================================================

The previous response did not respect the instructions.

It contained prescriptive or recommendation-oriented language.

Detected violations:

{violations_text}

Previous response:

{rejected_result}


Rewrite the entire response.

Preserve only conclusions supported by the established
developments and supporting content.

Remove every recommendation, instruction, obligation and call
to action.

Describe what the developments affect.

Do not tell the reader how to respond.

Do not claim that advertiser ROAS improves publisher CPM,
publisher yield or publisher revenue.

Do not claim that a profile metric will improve unless the
provided evidence establishes that effect for the same actor.

When a causal effect is not established, describe the issue as
a decision or measurement question.

Return only the corrected implications in the originally
requested format.
""".strip()


# ============================================================
# RUN CAPABILITY
# ============================================================

def _run_capability_prompt(
    prompt: str,
) -> str:

    return run_llm(
        prompt=prompt,
        temperature=(
            CAPABILITY_TEMPERATURE
        ),
    )


# ============================================================
# EXECUTE IMPLICATIONS
# ============================================================

def _execute_implications(
    prompt: str,
) -> str:

    current_prompt = prompt

    for _ in range(
        IMPLICATIONS_MAX_ATTEMPTS
    ):

        result = _run_capability_prompt(
            current_prompt
        )

        if not result:

            return ""

        violations = (
            _find_forbidden_implication_patterns(
                result
            )
        )

        if not violations:

            return result

        current_prompt = (
            _build_implications_correction_prompt(

                original_prompt=prompt,

                rejected_result=result,

                violations=violations,

            )
        )

    # Ne pas publier un texte qui enfreint encore
    # explicitement les règles éditoriales.
    return ""

# ============================================================
# EXECUTE CAPABILITY
# ============================================================

def execute_capability(
    expertise: Expertise,
    capability: str,
    context: dict | None = None,
) -> str:

    if expertise.count == 0:

        return ""

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = _build_prompt(

        capability=capability,

        expertise=expertise,

        context=context,

    )

    # ========================================================
    # IMPLICATIONS WITH VALIDATION
    # ========================================================

    if capability == CAPABILITY_IMPLICATIONS:

        return _execute_implications(
            prompt
        )

    # ========================================================
    # STANDARD CAPABILITY
    # ========================================================

    result = _run_capability_prompt(
        prompt
    )

    return result or ""

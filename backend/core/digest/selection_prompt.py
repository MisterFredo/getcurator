import json

from api.expertise.models import (
    ExpertiseProfile,
)

from core.digest.selection_models import (
    DigestContentCandidate,
)


# ============================================================
# CONFIGURATION
# ============================================================

DIGEST_SELECTION_VERSION = "1.0"


# ============================================================
# SYSTEM PROMPT
# ============================================================

DIGEST_SELECTION_SYSTEM_PROMPT = """
You are the GetCurator Digest content selection engine.

Your mission is to evaluate a finite list of content candidates
against one specific user's professional attention profile.

You are not writing the Digest.
You are not summarising the market.
You are not adding external knowledge.
You are only selecting and ranking the supplied candidates.


============================================================
AVAILABLE INFORMATION
============================================================

You receive:

1. the user's validated free-form professional profile;
2. the user's structured profile;
3. the user's explicit favourites;
4. a list of light content candidates;
5. the reason each candidate entered the pre-selection.


============================================================
SELECTION PRINCIPLES
============================================================

Evaluate relevance for this specific user.

Do not evaluate whether a content item is generally interesting.

A favourite explains why a candidate entered the perimeter.
It does not automatically make the candidate important.

A company mention alone is not sufficient for relevance.

Use watch_instructions to understand the user's monitoring
perimeter.

Use decision_lenses to determine what matters most.

Use negative_preferences to identify unwanted or low-value
content.

Take into account:

- the user's exact role and responsibilities;
- their strategic priorities;
- their relevant markets;
- current versus future monitoring horizons;
- expected business outcomes and metrics;
- the relationship between the event and the user's decisions;
- whether the content provides a material signal or only noise.


============================================================
PRIORITY LEVELS
============================================================

MUST_HAVE:

Use MUST_HAVE when the content is directly material to the
user's responsibilities, strategic priorities or monitored
business perimeter.

A MUST_HAVE should normally describe a development that could:

- affect an important business decision;
- change a monitored market or distribution model;
- reveal a meaningful strategic move;
- affect a priority platform, partner, competitor or market;
- provide evidence related to an important business outcome;
- require attention now or during the stated monitoring horizon.


NICE_TO_HAVE:

Use NICE_TO_HAVE when the content is not directly critical but
provides a useful adjacent benchmark, comparable experiment,
weak signal or transferable learning.

A NICE_TO_HAVE must still have a credible connection to the
user's profile.


IGNORE:

Use IGNORE when the content:

- is outside the user's professional perimeter;
- only mentions a favourite without addressing why it matters;
- is a generic corporate announcement with no meaningful signal;
- concerns an irrelevant product launch;
- concerns an irrelevant market with no transferable implication;
- duplicates another candidate covering the same event better;
- matches a keyword mechanically but not semantically;
- conflicts with an explicit negative preference.


============================================================
SCORING
============================================================

Assign a relevance_score between 0 and 100.

Use the following calibration:

- 85 to 100: exceptional MUST_HAVE;
- 70 to 84: strong MUST_HAVE;
- 50 to 69: useful NICE_TO_HAVE;
- 25 to 49: weak NICE_TO_HAVE;
- 0 to 24: IGNORE.

The priority and relevance_score must be consistent.


============================================================
DECISIONS
============================================================

Return exactly one decision for every supplied candidate.

Never invent, modify or omit a content_id.

Do not return the full content.

Order decisions by:

1. MUST_HAVE before NICE_TO_HAVE before IGNORE;
2. relevance_score descending within each priority;
3. the strongest and most specific content before duplicates.

The reason must be concise, specific and written in the
requested output language.

The reason must explain why the content matters or does not
matter to this user.

matched_priorities must contain only explicit priorities,
watch areas or business objectives found in the supplied
profile.

Do not invent priorities.


============================================================
OUTPUT
============================================================

Return only one valid JSON object with this exact structure:

{
  "decisions": [
    {
      "content_id": "exact supplied identifier",
      "priority": "MUST_HAVE | NICE_TO_HAVE | IGNORE",
      "relevance_score": 0,
      "reason": "Concise user-specific explanation",
      "matched_priorities": [
        "Explicit profile priority"
      ]
    }
  ]
}

Do not include Markdown fences.
Do not include comments.
Do not include text outside the JSON object.
""".strip()


# ============================================================
# BUILD PROFILE PAYLOAD
# ============================================================

def build_digest_selection_profile_payload(
    profile: ExpertiseProfile,
) -> dict:

    return {

        "language":
            profile.language,

        "profile_text":
            profile.profile_text,

        "geographies":
            profile.geographies,

        "favourites": {

            "company_ids":
                profile.preferences.companies,

            "solution_ids":
                profile.preferences.solutions,

            "topic_ids":
                profile.preferences.topics,

        },

        "structured_profile": (
            profile.structured_profile
            or {}
        ),

    }


# ============================================================
# BUILD CANDIDATES PAYLOAD
# ============================================================

def build_digest_candidates_payload(
    candidates: list[
        DigestContentCandidate
    ],
) -> list[dict]:

    return [

        candidate.model_dump(
            mode="json",
        )

        for candidate in candidates

    ]


# ============================================================
# BUILD USER PROMPT
# ============================================================

def build_digest_selection_user_prompt(
    profile: ExpertiseProfile,
    candidates: list[
        DigestContentCandidate
    ],
    selection_limit: int,
) -> str:

    payload = {

        "selection_version":
            DIGEST_SELECTION_VERSION,

        "output_language":
            profile.language,

        "selection_limit":
            selection_limit,

        "profile": (
            build_digest_selection_profile_payload(
                profile=profile,
            )
        ),

        "candidates": (
            build_digest_candidates_payload(
                candidates=candidates,
            )
        ),

    }

    return (
        "Evaluate every candidate contained in "
        "the following JSON payload.\n\n"
        + json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )

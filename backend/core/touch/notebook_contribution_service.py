from core.touch.notebook_models import (
    TouchNotebookRequest,
)

from core.touch.notebook_utils import (
    unique_ids,
)


# ============================================================
# NORMALIZE STATEMENT
# ============================================================

def _normalize_statement(
    value: str,
) -> str:

    return (
        value
        or ""
    ).strip()


# ============================================================
# BUILD CONTRIBUTION BATCHES
# ============================================================

def build_contribution_batches(
    request: TouchNotebookRequest,
) -> list[dict]:

    allowed_content_ids = set(
        request.content_ids
    )

    seen_statements_by_content: set[
        tuple[str, str]
    ] = set()

    notes = []

    contribution_index = 0

    for contribution in (
        request.contributions
    ):

        content_id = (
            contribution
            .content_id
            .strip()
        )

        if (
            content_id
            not in allowed_content_ids
        ):

            raise ValueError(
                "Une contribution référence un "
                "contenu extérieur au corpus : "
                f"{content_id}"
            )

        statements = unique_ids([

            _normalize_statement(
                statement
            )

            for statement
            in contribution.statements

        ])

        if not statements:

            raise ValueError(
                "Un contenu sélectionné ne possède "
                "aucune contribution exploitable : "
                f"{content_id}"
            )

        for statement in statements:

            statement_key = (
                content_id,
                statement,
            )

            if (
                statement_key
                in seen_statements_by_content
            ):

                continue

            seen_statements_by_content.add(
                statement_key
            )

            contribution_index += 1

            notes.append({
                "temporary_note_id": (
                    "contribution-"
                    f"{contribution_index:04d}"
                ),

                "note_type":
                    "FACT",

                "statement":
                    statement,

                "explanation":
                    "",

                "actors":
                    [],

                "geographies":
                    [],

                "dates":
                    [],

                "confidence":
                    "MEDIUM",

                "status":
                    "VALIDATED",

                "source_content_ids": [
                    content_id,
                ],
            })

    if not notes:

        raise ValueError(
            "Le corpus sélectionné ne contient "
            "aucune contribution"
        )

    return [
        {
            "notes":
                notes,
        }
    ]

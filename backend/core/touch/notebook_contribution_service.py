from core.touch.notebook_models import (
    TouchEvidenceNote,
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
# BUILD CONTRIBUTION NOTES
# ============================================================

def build_contribution_notes(
    request: TouchNotebookRequest,
) -> list[TouchEvidenceNote]:

    allowed_content_ids = set(
        request.content_ids
    )

    supplied_content_ids: set[str] = set()

    contribution_records: dict[str, dict] = {}

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

        supplied_content_ids.add(
            content_id
        )

        statements = unique_ids([

            _normalize_statement(
                statement
            )

            for statement
            in contribution.statements

            if _normalize_statement(
                statement
            )

        ])

        if not statements:

            raise ValueError(
                "Un contenu sélectionné ne possède "
                "aucune contribution exploitable : "
                f"{content_id}"
            )

        for statement in statements:

            contribution_index += 1

            input_note_id = (
                "contribution-"
                f"{contribution_index:04d}"
            )

            # Exact deterministic deduplication.
            # The original wording is preserved.
            statement_key = (
                statement.casefold()
            )

            existing_record = (
                contribution_records.get(
                    statement_key
                )
            )

            if existing_record:

                existing_record[
                    "input_note_ids"
                ].append(
                    input_note_id
                )

                existing_record[
                    "source_content_ids"
                ].append(
                    content_id
                )

                continue

            contribution_records[
                statement_key
            ] = {

                "statement":
                    statement,

                "input_note_ids": [
                    input_note_id,
                ],

                "source_content_ids": [
                    content_id,
                ],

            }

    missing_content_ids = (
        allowed_content_ids
        - supplied_content_ids
    )

    if missing_content_ids:

        raise ValueError(
            "Certains contenus sélectionnés ne "
            "possèdent aucune contribution : "
            + ", ".join(
                sorted(
                    missing_content_ids
                )
            )
        )

    if not contribution_records:

        raise ValueError(
            "Le corpus sélectionné ne contient "
            "aucune contribution"
        )

    notes = []

    for note_index, record in enumerate(
        contribution_records.values(),
        start=1,
    ):

        notes.append(

            TouchEvidenceNote(

                note_id=(
                    f"note-{note_index:03d}"
                ),

                input_note_ids=(
                    unique_ids(
                        record[
                            "input_note_ids"
                        ]
                    )
                ),

                note_type=
                    "FACT",

                statement=(
                    record[
                        "statement"
                    ]
                ),

                explanation=
                    "",

                actors=[],

                geographies=[],

                dates=[],

                confidence=
                    "MEDIUM",

                status=
                    "VALIDATED",

                source_content_ids=(
                    unique_ids(
                        record[
                            "source_content_ids"
                        ]
                    )
                ),

            )

        )

    return notes

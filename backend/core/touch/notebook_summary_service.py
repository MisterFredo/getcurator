import re

from typing import (
    Any,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
    TouchNotebookExecutiveSummaryItem,
    TouchNotebookRequest,
)

from core.touch.notebook_summary_prompt import (
    TOUCH_NOTEBOOK_SUMMARY_SYSTEM_PROMPT,
    build_touch_notebook_summary_prompt,
)

from core.touch.notebook_utils import (
    build_retry_prompt,
    extract_json_object,
    unique_ids,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# INTERNAL MODELS
# ============================================================

class TouchNotebookSummaryDraftItem(
    BaseModel,
):

    statement: str

    note_ids: list[str] = Field(
        default_factory=list,
    )

    class Config:

        extra = "forbid"


class TouchNotebookSummaryResult(
    BaseModel,
):

    items: list[
        TouchNotebookSummaryDraftItem
    ] = Field(
        default_factory=list,
    )

    class Config:

        extra = "forbid"


# ============================================================
# NORMALIZE STRING LIST
# ============================================================

def _normalize_string_list(
    value: Any,
) -> list[str]:

    if value is None:

        return []

    if isinstance(
        value,
        str,
    ):

        normalized_value = (
            value.strip()
        )

        return (
            [normalized_value]
            if normalized_value
            else []
        )

    if not isinstance(
        value,
        list,
    ):

        return []

    return unique_ids([

        str(item).strip()

        for item in value

        if (
            item is not None
            and str(item).strip()
        )

    ])


# ============================================================
# NORMALIZE ITEM
# ============================================================

def _normalize_item(
    raw_item: Any,
) -> dict:

    if not isinstance(
        raw_item,
        dict,
    ):

        raise ValueError(
            "Un élément de l’Executive Summary "
            "n’est pas un objet JSON"
        )

    return {

        "statement":
            str(
                raw_item.get(
                    "statement"
                )
                or ""
            ).strip(),

        "note_ids":
            _normalize_string_list(
                raw_item.get(
                    "note_ids"
                )
            ),

    }


# ============================================================
# NORMALIZE PAYLOAD
# ============================================================

def _normalize_payload(
    parsed: dict,
) -> dict:

    raw_items = (
        parsed.get(
            "items",
            [],
        )
        or []
    )

    if not isinstance(
        raw_items,
        list,
    ):

        raise ValueError(
            "Le champ items de l’Executive "
            "Summary doit être une liste"
        )

    return {

        "items": [

            _normalize_item(
                raw_item
            )

            for raw_item
            in raw_items

        ],

    }


# ============================================================
# COUNT WORDS
# ============================================================

def _count_words(
    value: str,
) -> int:

    words = re.findall(
        (
            r"\b[\wÀ-ÖØ-öø-ÿ]+"
            r"(?:[’'-][\wÀ-ÖØ-öø-ÿ]+)*\b"
        ),
        value,
    )

    return len(
        words
    )


# ============================================================
# VALIDATE SUMMARY
# ============================================================

def _validate_summary(
    result: TouchNotebookSummaryResult,
    notebook: TouchCorpusNotebook,
) -> None:

    available_note_ids = {

        note.note_id

        for note in notebook.notes

    }

    available_note_count = len(
        available_note_ids
    )

    if available_note_count == 0:

        raise ValueError(
            "Le notebook ne contient aucune note "
            "pour construire l’Executive Summary"
        )

    minimum_item_count = (
        4
        if available_note_count >= 4
        else available_note_count
    )

    maximum_item_count = min(
        6,
        available_note_count,
    )

    item_count = len(
        result.items
    )

    if (
        item_count < minimum_item_count
        or item_count > maximum_item_count
    ):

        raise ValueError(
            "L’Executive Summary doit contenir "
            f"entre {minimum_item_count} et "
            f"{maximum_item_count} éléments. "
            f"Valeur reçue : {item_count}"
        )

    used_note_ids = set()

    unknown_note_ids = set()

    duplicated_note_ids = set()

    empty_item_indexes = []

    invalid_length_indexes = []

    for item_index, item in enumerate(
        result.items,
        start=1,
    ):

        if (
            not item.statement
            or not item.note_ids
        ):

            empty_item_indexes.append(
                str(
                    item_index
                )
            )

            continue

        word_count = _count_words(
            item.statement
        )

        # A small tolerance is accepted around the
        # editorial target of 30 to 55 words.
        if word_count > 70:

            invalid_length_indexes.append(
                (
                    item_index,
                    word_count,
                )
            )

        for note_id in item.note_ids:

            if (
                note_id
                not in available_note_ids
            ):

                unknown_note_ids.add(
                    note_id
                )

                continue

            if note_id in used_note_ids:

                duplicated_note_ids.add(
                    note_id
                )

            used_note_ids.add(
                note_id
            )

    if empty_item_indexes:

        raise ValueError(
            "Certains éléments de l’Executive "
            "Summary sont incomplets : "
            + ", ".join(
                empty_item_indexes
            )
        )

    if invalid_length_indexes:

        details = "; ".join(

            (
                f"item-{item_index} "
                f"({word_count} mots)"
            )

            for (
                item_index,
                word_count,
            )
            in invalid_length_indexes

        )

        raise ValueError(
            "Certains éléments de l’Executive "
            "Summary ont une longueur invalide : "
            f"{details}"
        )

    if unknown_note_ids:

        raise ValueError(
            "L’Executive Summary référence des "
            "note_id inconnus : "
            + ", ".join(
                sorted(
                    unknown_note_ids
                )
            )
        )

    if duplicated_note_ids:

        raise ValueError(
            "Certaines notes sont utilisées dans "
            "plusieurs éléments de l’Executive "
            "Summary : "
            + ", ".join(
                sorted(
                    duplicated_note_ids
                )
            )
        )


# ============================================================
# BUILD SUMMARY ITEMS
# ============================================================

def _build_summary_items(
    result: TouchNotebookSummaryResult,
    notebook: TouchCorpusNotebook,
) -> list[
    TouchNotebookExecutiveSummaryItem
]:

    notes_by_id = {

        note.note_id:
            note

        for note in notebook.notes

    }

    summary_items = []

    for item_index, item in enumerate(
        result.items,
        start=1,
    ):

        source_content_ids = unique_ids([

            content_id

            for note_id in item.note_ids

            for content_id
            in notes_by_id[
                note_id
            ].source_content_ids

        ])

        summary_items.append(

            TouchNotebookExecutiveSummaryItem(

                summary_id=(
                    f"summary-{item_index:03d}"
                ),

                statement=(
                    item.statement.strip()
                ),

                note_ids=(
                    unique_ids(
                        item.note_ids
                    )
                ),

                source_content_ids=(
                    source_content_ids
                ),

            )

        )

    return summary_items


# ============================================================
# BUILD EXECUTIVE SUMMARY
# ============================================================

def build_notebook_executive_summary(
    request: TouchNotebookRequest,
    notebook: TouchCorpusNotebook,
    model: Optional[str] = None,
    max_attempts: int = 2,
) -> TouchCorpusNotebook:

    if not notebook.notes:

        raise ValueError(
            "Le notebook ne contient aucune note "
            "pour construire l’Executive Summary"
        )

    original_prompt = (
        build_touch_notebook_summary_prompt(

            request=request,

            notebook=notebook,

        )
    )

    prompt = original_prompt

    attempts = max(
        1,
        max_attempts,
    )

    last_error = (
        "Erreur inconnue pendant la génération "
        "de l’Executive Summary"
    )

    for attempt in range(
        attempts
    ):

        try:

            raw_content = run_llm_json(

                prompt=prompt,

                model=model,

                temperature=0.0,

                system_prompt=(
                    TOUCH_NOTEBOOK_SUMMARY_SYSTEM_PROMPT
                ),

            )

            parsed = extract_json_object(
                raw_content
            )

            normalized_payload = (
                _normalize_payload(
                    parsed
                )
            )

            result = (
                TouchNotebookSummaryResult
                .model_validate(
                    normalized_payload
                )
            )

            _validate_summary(

                result=result,

                notebook=notebook,

            )

            summary_items = (
                _build_summary_items(

                    result=result,

                    notebook=notebook,

                )
            )

            return notebook.model_copy(
                update={

                    "executive_summary":
                        summary_items,

                },
            )

        except Exception as exc:

            last_error = str(
                exc
            )

            if (
                attempt + 1
                >= attempts
            ):

                break

            prompt = build_retry_prompt(

                original_prompt=(
                    original_prompt
                ),

                error=last_error,

            )

    raise ValueError(
        "Échec de la génération de "
        "l’Executive Summary après "
        f"{attempts} tentative(s) : "
        f"{last_error}"
    )

from typing import (
    Optional,
)

from core.expertise.content_service import (
    load_contents_by_ids,
)

from core.numbers.content_service import (
    get_validated_numbers_for_contents,
)

from core.touch.notebook_contribution_service import (
    build_contribution_notes,
)

from core.touch.notebook_models import (
    TouchNotebookOutcome,
    TouchNotebookRequest,
)

from core.touch.notebook_numbers import (
    build_certified_numbers,
)

from core.touch.notebook_organization_service import (
    organize_notebook,
)

from core.touch.notebook_plan_service import (
    prepare_notebook,
    validate_executive_summary,
)

from core.touch.notebook_summary_service import (
    build_notebook_executive_summary,
)

from core.touch.notebook_utils import (
    normalize_language,
    unique_ids,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_NOTEBOOK_ATTEMPTS = 2


# ============================================================
# NORMALIZE REQUEST
# ============================================================

def _normalize_request(
    request: TouchNotebookRequest,
) -> TouchNotebookRequest:

    content_ids = unique_ids(
        request.content_ids
    )

    if not content_ids:
        raise ValueError(
            "Le corpus Touch est vide"
        )

    subject = (
        request.subject
        or ""
    ).strip()

    if not subject:
        raise ValueError(
            "Le sujet du notebook Touch "
            "est obligatoire"
        )

    objective = (
        request.objective
        or ""
    ).strip()

    language = normalize_language(
        request.output_language
    )

    return request.model_copy(
        update={
            "subject": subject,
            "objective": objective,
            "content_ids": content_ids,
            "output_language": language,
        },
    )


# ============================================================
# VALIDATE SELECTED CONTENTS
# ============================================================

def _validate_selected_contents(
    request: TouchNotebookRequest,
):

    contents = load_contents_by_ids(
        content_ids=request.content_ids,
        language=request.output_language,
    )

    contents_by_id = {
        content.id: content
        for content in contents
    }

    missing_content_ids = [
        content_id
        for content_id in request.content_ids
        if content_id not in contents_by_id
    ]

    if missing_content_ids:
        raise ValueError(
            "Certains contenus Touch sont "
            "introuvables : "
            + ", ".join(
                missing_content_ids
            )
        )

    return [
        contents_by_id[content_id]
        for content_id in request.content_ids
    ]


# ============================================================
# LOAD CERTIFIED NUMBERS
# ============================================================

def _load_certified_numbers(
    request: TouchNotebookRequest,
):

    numbers_by_content = (
        get_validated_numbers_for_contents(
            content_ids=request.content_ids,
        )
    )

    return build_certified_numbers(
        content_ids=request.content_ids,
        numbers_by_content=numbers_by_content,
    )


# ============================================================
# BUILD TOUCH NOTEBOOK
# ============================================================

def build_touch_notebook(
    request: TouchNotebookRequest,
    model: Optional[str] = None,
) -> TouchNotebookOutcome:

    try:

        normalized_request = (
            _normalize_request(
                request
            )
        )

        # ====================================================
        # 1. VALIDATE SELECTED CORPUS
        # ====================================================

        selected_contents = (
            _validate_selected_contents(
                normalized_request
            )
        )

        # ====================================================
        # 2. LOAD CANONICAL CERTIFIED NUMBERS
        # ====================================================

        certified_numbers = (
            _load_certified_numbers(
                normalized_request
            )
        )

        # ====================================================
        # 3. BUILD NOTES FROM ORIGINAL CONTRIBUTIONS
        # ====================================================

        contribution_notes = (
            build_contribution_notes(
                request=normalized_request,
            )
        )

        # ====================================================
        # 4. ORGANIZE DOCUMENTARY PLAN
        # ====================================================

        notebook = organize_notebook(
            request=normalized_request,
            notes=contribution_notes,
            certified_numbers=certified_numbers,
            model=model,
            max_attempts=(
                DEFAULT_TOUCH_NOTEBOOK_ATTEMPTS
            ),
        )

        # ====================================================
        # 5. REPAIR AND VALIDATE FINAL PLAN
        # ====================================================

        notebook = prepare_notebook(
            notebook=notebook,
            allowed_content_ids=set(
                normalized_request.content_ids
            ),
        )

        # ====================================================
        # 6. BUILD EVIDENCE-GROUNDED EXECUTIVE SUMMARY
        # ====================================================

        notebook = build_notebook_executive_summary(
            request=normalized_request,
            notebook=notebook,
            model=model,
            max_attempts=(
                DEFAULT_TOUCH_NOTEBOOK_ATTEMPTS
            ),
        )

        # ====================================================
        # 7. VALIDATE SUMMARY REFERENCES AND SOURCES
        # ====================================================

        validate_executive_summary(
            notebook=notebook,
            allowed_content_ids=set(
                normalized_request.content_ids
            ),
        )

        return TouchNotebookOutcome(
            status="GENERATED",
            notebook=notebook,
            source_count=len(
                selected_contents
            ),
            error=None,
        )

    except Exception as exc:

        return TouchNotebookOutcome(
            status="GENERATION_FAILED",
            notebook=None,
            source_count=0,
            error=str(exc)[:2000],
        )

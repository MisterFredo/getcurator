from time import (
    perf_counter,
)

from typing import (
    Optional,
)

from core.touch.candidate_service import (
    DEFAULT_TOUCH_CANDIDATE_LIMIT_PER_POOL,
    DEFAULT_TOUCH_TOTAL_CANDIDATE_LIMIT,
    build_touch_candidates,
)

from core.touch.consolidation_engine import (
    consolidate_touch_evaluation,
)

from core.touch.evaluation_engine import (
    DEFAULT_TOUCH_EVALUATION_BATCH_SIZE,
    evaluate_touch_candidates,
)

from core.touch.search_engine import (
    interpret_touch_research_brief,
)

from core.touch.search_models import (
    TouchSearchOutcome,
    TouchResearchBrief,
)


# ============================================================
# SEARCH TOUCH CONTENTS
# ============================================================

def search_touch_contents(
    brief: TouchResearchBrief,
    model: Optional[str] = None,
    candidate_limit_per_pool: int = (
        DEFAULT_TOUCH_CANDIDATE_LIMIT_PER_POOL
    ),
    total_candidate_limit: int = (
        DEFAULT_TOUCH_TOTAL_CANDIDATE_LIMIT
    ),
    evaluation_batch_size: int = (
        DEFAULT_TOUCH_EVALUATION_BATCH_SIZE
    ),
) -> TouchSearchOutcome:

    started_at = perf_counter()

    errors: list[str] = []

    used_fallback = False

    # ========================================================
    # INTERPRET RESEARCH BRIEF
    # ========================================================

    interpretation_started_at = (
        perf_counter()
    )

    (
        interpretation,
        interpretation_used_fallback,
        interpretation_error,
    ) = interpret_touch_research_brief(

        brief=brief,

        model=model,

    )

    if interpretation_used_fallback:

        used_fallback = True

    if interpretation_error:

        errors.append(

            "Interprétation Touch : "
            f"{interpretation_error}"

        )

    interpretation_finished_at = (
        perf_counter()
    )

    # ========================================================
    # BUILD CANDIDATES
    # ========================================================

    candidates_started_at = (
        perf_counter()
    )

    candidates, candidate_errors = (
        build_touch_candidates(

            brief=brief,

            interpretation=(
                interpretation
            ),

            candidate_limit_per_pool=(
                candidate_limit_per_pool
            ),

            total_candidate_limit=(
                total_candidate_limit
            ),

        )
    )

    errors.extend(
        candidate_errors
    )

    candidates_finished_at = (
        perf_counter()
    )

    # ========================================================
    # EVALUATE CANDIDATES
    # ========================================================

    evaluation_started_at = (
        perf_counter()
    )

    evaluation, evaluation_errors = (
        evaluate_touch_candidates(

            brief=brief,

            interpretation=(
                interpretation
            ),

            candidates=candidates,

            model=model,

            batch_size=(
                evaluation_batch_size
            ),

        )
    )

    errors.extend(
        evaluation_errors
    )

    evaluation_finished_at = (
        perf_counter()
    )

    # ========================================================
    # CONSOLIDATE EVALUATION
    # ========================================================

    consolidation_started_at = (
        perf_counter()
    )

    (
        consolidation,
        consolidation_used_fallback,
        consolidation_error,
    ) = consolidate_touch_evaluation(

        brief=brief,

        interpretation=(
            interpretation
        ),

        candidates=candidates,

        evaluation=evaluation,

        model=model,

    )

    if consolidation_used_fallback:

        used_fallback = True

    if consolidation_error:

        errors.append(

            "Consolidation Touch : "
            f"{consolidation_error}"

        )

    consolidation_finished_at = (
        perf_counter()
    )

    # ========================================================
    # MONITORING
    # ========================================================

    finished_at = perf_counter()

    print(
        "TOUCH_SEARCH",
        {

            "subject":
                interpretation.subject,

            "search_terms":
                interpretation.search_terms,

            "related_angles":
                interpretation.related_angles,

            "candidate_count":
                len(
                    candidates
                ),

            "evaluated_count":
                len(
                    evaluation.decisions
                ),

            "event_group_count":
                len(
                    consolidation.event_groups
                ),

            "error_count":
                len(
                    errors
                ),

            "used_fallback":
                used_fallback,

            "interpretation_seconds":
                round(
                    (
                        interpretation_finished_at
                        - interpretation_started_at
                    ),
                    3,
                ),

            "candidates_seconds":
                round(
                    (
                        candidates_finished_at
                        - candidates_started_at
                    ),
                    3,
                ),

            "evaluation_seconds":
                round(
                    (
                        evaluation_finished_at
                        - evaluation_started_at
                    ),
                    3,
                ),

            "consolidation_seconds":
                round(
                    (
                        consolidation_finished_at
                        - consolidation_started_at
                    ),
                    3,
                ),

            "total_seconds":
                round(
                    (
                        finished_at
                        - started_at
                    ),
                    3,
                ),

        },
    )

    # ========================================================
    # OUTCOME
    # ========================================================

    return TouchSearchOutcome(

        interpretation=interpretation,

        candidates=candidates,

        evaluation=evaluation,

        consolidation=consolidation,

        used_fallback=used_fallback,

        errors=errors,

    )

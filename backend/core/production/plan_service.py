from datetime import datetime, timezone

from core.production.models import (
    ProductionEditorialPlan,
    ProductionPlanSnapshot,
    ProductionPreparedCorpus,
)

from core.production.plan_prompt import (
    PRODUCTION_PLAN_SYSTEM_PROMPT,
    build_plan_evidence_aliases,
    build_production_plan_prompt,
)

from core.production.repository import (
    get_production,
)

from core.touch.notebook_utils import (
    build_retry_prompt,
    extract_json_object,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# VALIDATE PLAN AGAINST SAVED CORPUS
# ============================================================

def validate_production_plan(
    plan: ProductionEditorialPlan,
    corpus: ProductionPreparedCorpus,
) -> None:
    expected_page_count = (
        corpus.request.target_page_count
    )

    if (
        expected_page_count is not None
        and len(plan.pages) != expected_page_count
    ):
        raise ValueError(
            "Le plan doit contenir exactement "
            f"{expected_page_count} pages, "
            "couverture et sources comprises. "
            f"Reçu : {len(plan.pages)}."
        )

    references = {
        item.reference_id: item
        for item in corpus.evidence_index
    }

    if len(references) != len(
        corpus.evidence_index
    ):
        raise ValueError(
            "Le socle contient des références "
            "de preuve dupliquées."
        )

    if sum(
        page.layout == "SOURCES"
        for page in plan.pages
    ) != 1:
        raise ValueError(
            "Le plan doit contenir "
            "une seule page SOURCES."
        )

    for page in plan.pages:
        evidence_ids = set(
            page.evidence_reference_ids
        )

        number_ids = set(
            page.number_reference_ids
        )

        unknown_ids = (
            evidence_ids | number_ids
        ) - set(references)

        if unknown_ids:
            raise ValueError(
                f"Page {page.page_id} : "
                "références inconnues : "
                + ", ".join(
                    sorted(unknown_ids)
                )
            )

        invalid_numbers = {
            reference_id
            for reference_id in number_ids
            if (
                references[
                    reference_id
                ].kind != "NUMBER"
            )
        }

        if invalid_numbers:
            raise ValueError(
                f"Page {page.page_id} : "
                "certaines références de Numbers "
                "ne désignent pas des NUMBER."
            )

        if not number_ids.issubset(
            evidence_ids
        ):
            raise ValueError(
                f"Page {page.page_id} : "
                "chaque Number doit aussi être "
                "référencé dans "
                "evidence_reference_ids."
            )

        # Prevent numeric references from bypassing
        # the dedicated Numbers selection.
        evidence_number_ids = {
            reference_id
            for reference_id in evidence_ids
            if (
                references[
                    reference_id
                ].kind == "NUMBER"
            )
        }

        if evidence_number_ids != number_ids:
            raise ValueError(
                f"Page {page.page_id} : "
                "les références NUMBER doivent "
                "également figurer dans "
                "number_reference_ids."
            )

        if page.layout not in {
            "COVER",
            "SOURCES",
        }:
            if not evidence_ids:
                raise ValueError(
                    f"Page {page.page_id} : "
                    "aucune preuve sélectionnée."
                )

            if not any(
                item.strip()
                for item
                in page.explanation_outline
            ):
                raise ValueError(
                    f"Page {page.page_id} : "
                    "le raisonnement à développer "
                    "est absent."
                )

        if page.layout in {
            "CHART_WITH_ANALYSIS",
            "KEY_NUMBERS",
        }:
            if not number_ids:
                raise ValueError(
                    f"Page {page.page_id} : "
                    "ce format nécessite "
                    "au moins un Number."
                )

            if not page.visual_intent.strip():
                raise ValueError(
                    f"Page {page.page_id} : "
                    "la représentation visuelle "
                    "doit être décrite."
                )


def _restore_plan_references(
    plan: ProductionEditorialPlan,
    corpus: ProductionPreparedCorpus,
) -> ProductionEditorialPlan:
    aliases = build_plan_evidence_aliases(
        corpus
    )

    original_ids = {
        reference.reference_id
        for reference
        in corpus.evidence_index
    }

    def restore(
        values: list[str],
    ) -> list[str]:
        result = []

        for value in values:
            if value in aliases:
                original = aliases[value]

            elif value in original_ids:
                original = value

            else:
                raise ValueError(
                    "Référence de preuve inconnue : "
                    f"{value}. Utilise uniquement "
                    "les reference_id du catalogue "
                    "(E00001, E00002, etc.)."
                )

            if original not in result:
                result.append(original)

        return result

    payload = plan.model_dump(
        mode="json",
    )

    references_by_id = {
        reference.reference_id: reference
        for reference
        in corpus.evidence_index
    }

    for page in payload["pages"]:
        evidence_ids = restore(
            page["evidence_reference_ids"]
        )

        number_ids = restore(
            page["number_reference_ids"]
        )

        # Include explicitly selected Numbers
        # in the page's evidence.
        for reference_id in number_ids:
            if reference_id not in evidence_ids:
                evidence_ids.append(reference_id)

        # Include evidence of kind NUMBER
        # in the dedicated Numbers selection.
        for reference_id in evidence_ids:
            if (
                references_by_id[
                    reference_id
                ].kind == "NUMBER"
                and reference_id not in number_ids
            ):
                number_ids.append(reference_id)

        page["evidence_reference_ids"] = (
            evidence_ids
        )

        page["number_reference_ids"] = (
            number_ids
        )

    return (
        ProductionEditorialPlan.model_validate(
            payload
        )
    )

# ============================================================
# GENERATE PLAN FROM SAVED PRODUCTION
# ============================================================

def generate_production_plan(
    production_id: str,
    model: str | None = None,
    max_attempts: int = 2,
) -> ProductionPlanSnapshot:
    production = get_production(
        production_id=production_id,
    )

    if production is None:
        raise ValueError(
            "Production introuvable."
        )

    corpus = (
        ProductionPreparedCorpus.model_validate(
            production["corpus"]
        )
    )

    original_prompt = (
        build_production_plan_prompt(
            corpus=corpus,
        )
    )

    prompt = original_prompt

    attempts = min(
        max(max_attempts, 1),
        3,
    )

    last_error = (
        "Erreur inconnue pendant "
        "la génération du plan."
    )

    for attempt in range(attempts):
        try:
            raw_content = run_llm_json(
                prompt=prompt,
                model=model,
                temperature=0.0,
                system_prompt=(
                    PRODUCTION_PLAN_SYSTEM_PROMPT
                ),
            )

            parsed = extract_json_object(
                raw_content
            )

            plan = (
                ProductionEditorialPlan.model_validate(
                    parsed
                )
            )

            plan = _restore_plan_references(
                plan=plan,
                corpus=corpus,
            )

            validate_production_plan(
                plan=plan,
                corpus=corpus,
            )

            return ProductionPlanSnapshot(
                production_id=(
                    corpus.production_id
                ),
                corpus_sha256=(
                    corpus.corpus_sha256
                ),
                generated_at=datetime.now(
                    timezone.utc,
                ),
                plan=plan,
            )

        except Exception as exc:
            last_error = str(exc)[:4000]

            if attempt + 1 >= attempts:
                break

            prompt = build_retry_prompt(
                original_prompt=original_prompt,
                error=last_error,
            )

    raise ValueError(
        "Échec de la génération du plan "
        f"après {attempts} tentative(s) : "
        f"{last_error}"
    )

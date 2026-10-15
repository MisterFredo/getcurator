import logging
import os
import json


from datetime import datetime, timezone

from core.production.plan_prompt import (
    PRODUCTION_PLAN_SYSTEM_PROMPT,
    PRODUCTION_SELECTION_SYSTEM_PROMPT,
    build_plan_evidence_aliases,
    build_production_plan_prompt,
    build_production_selection_prompt,
)


from core.production.models import (
    ProductionEditorialPlan,
    ProductionPlanSnapshot,
    ProductionPreparedCorpus,
    ProductionEditorialSelection,
)


from core.production.repository import (
    get_production,
)

from core.touch.notebook_utils import (
    extract_json_object,
)

from utils.llm import (
    run_llm_json,
)
logger = logging.getLogger(__name__)


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

            if not evidence_ids:
                raise ValueError(
                    f"Page {page.page_id}, "
                    f"titre={page.title!r}, "
                    f"layout={page.layout} : "
                    "aucune preuve sélectionnée. "
                    "Ajoute dans evidence_reference_ids "
                    "les références fournies qui "
                    "soutiennent directement le message. "
                    "Pour une page IMPLICATIONS, cite "
                    "les constats dont découlent "
                    "les décisions proposées. "
                    "Si aucun constat ne les justifie, "
                    "supprime ou reformule la page."
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

    references_by_id = {
        reference.reference_id: reference
        for reference
        in corpus.evidence_index
    }

    def restore(
        values: list[str],
    ) -> list[str]:
        result: list[str] = []

        for value in values:
            if value in aliases:
                original = aliases[value]

            elif value in references_by_id:
                original = value

            else:
                raise ValueError(
                    "Référence de preuve inconnue : "
                    f"{value}. Utilise uniquement "
                    "les reference_id du catalogue."
                )

            if original not in result:
                result.append(original)

        return result

    payload = plan.model_dump(
        mode="json",
    )

    for page in payload["pages"]:
        evidence_ids = restore(
            page["evidence_reference_ids"]
        )

        proposed_number_ids = restore(
            page["number_reference_ids"]
        )

        # Preserve every selected proof, including
        # proofs incorrectly classified as Numbers.
        for reference_id in proposed_number_ids:
            if reference_id not in evidence_ids:
                evidence_ids.append(reference_id)

        # The saved evidence type determines whether
        # a reference is actually a Number.
        number_ids = [
            reference_id
            for reference_id in evidence_ids
            if (
                references_by_id[
                    reference_id
                ].kind == "NUMBER"
            )
        ]

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

def _generate_validated_json(
    *,
    original_prompt: str,
    system_prompt: str,
    response_model,
    validate,
    model: str,
    attempts: int,
    stage: str,
):
    prompt = original_prompt
    errors: list[str] = []

    for attempt in range(attempts):
        raw_content = ""

        try:
            raw_content = run_llm_json(
                prompt=prompt,
                model=model,
                temperature=0.0,
                system_prompt=system_prompt,
            )

            if not raw_content.strip():
                raise ValueError(
                    "Le LLM n'a renvoyé aucun "
                    "contenu exploitable."
                )

            result = response_model.model_validate(
                extract_json_object(
                    raw_content
                )
            )

            validate(result)

            return result

        except Exception as exc:
            error = str(exc)[:4000]
            errors.append(error)

            logger.warning(
                "Production stage=%s "
                "attempt=%s/%s failed: %s",
                stage,
                attempt + 1,
                attempts,
                error,
            )

            if attempt + 1 < attempts:
                correction = {
                    "stage": stage,
                    "validation_errors": errors,
                    "previous_response": raw_content,
                    "instructions": [
                        (
                            "Corrige la réponse précédente "
                            "en respectant le schéma et "
                            "toutes les consignes initiales."
                        ),
                        (
                            "Conserve les éléments valides, "
                            "sauf si leur modification est "
                            "nécessaire pour corriger "
                            "les erreurs."
                        ),
                        (
                            "Utilise uniquement les "
                            "reference_id E00001, etc., "
                            "fournis pour cette étape."
                        ),
                        (
                            "N'invente aucune référence "
                            "et aucun chiffre."
                        ),
                        (
                            "Respecte target_page_count "
                            "s'il est renseigné."
                        ),
                        (
                            "Si une page ne dispose pas "
                            "de NUMBER pertinent, choisis "
                            "un format adapté plutôt que "
                            "d'ajouter un chiffre hors sujet."
                        ),
                        (
                            "Retourne uniquement "
                            "l'objet JSON complet corrigé."
                        ),
                    ],
                }

                prompt = (
                    original_prompt
                    + "\n\nCORRECTION REQUISE\n"
                    + json.dumps(
                        correction,
                        ensure_ascii=False,
                    )
                )

    raise ValueError(
        f"Échec de l'étape {stage} "
        f"après {attempts} tentative(s) : "
        f"{errors[-1]}"
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

    # Separate configuration for Production.
    # Does not change the shared LLM default.
    selected_model = (
        model
        or os.getenv("PRODUCTION_LLM_MODEL")
        or "gpt-4o"
    )

    attempts = min(
        max(max_attempts, 1),
        3,
    )

    aliases = build_plan_evidence_aliases(
        corpus
    )

    def validate_selection(
        selection: ProductionEditorialSelection,
    ) -> None:
        for finding in selection.findings:
            unknown = (
                set(
                    finding
                    .evidence_reference_ids
                )
                - set(aliases)
            )

            if unknown:
                raise ValueError(
                    f"Constat {finding.finding_id} : "
                    "références inconnues : "
                    + ", ".join(
                        sorted(unknown)
                    )
                )

    logger.info(
        "Production generation started: "
        "production_id=%s model=%s",
        production_id,
        selected_model,
    )

    selection = _generate_validated_json(
        original_prompt=(
            build_production_selection_prompt(
                corpus
            )
        ),
        system_prompt=(
            PRODUCTION_SELECTION_SYSTEM_PROMPT
        ),
        response_model=(
            ProductionEditorialSelection
        ),
        validate=validate_selection,
        model=selected_model,
        attempts=attempts,
        stage="selection_editoriale",
    )

    # Temporary diagnostic trace.
    # Contains report content: keep in internal logs.
    logger.info(
        "Production editorial selection: "
        "production_id=%s selection=%s",
        production_id,
        selection.model_dump_json(),
    )

    selected_original_ids = {
        aliases[reference_id]
        for finding in selection.findings
        for reference_id
        in finding.evidence_reference_ids
    }

    def validate_generated_plan(
        plan: ProductionEditorialPlan,
    ) -> None:
        restored = _restore_plan_references(
            plan=plan,
            corpus=corpus,
        )

        for page in restored.pages:
            unexpected = (
                set(
                    page.evidence_reference_ids
                )
                - selected_original_ids
            )

            if unexpected:
                raise ValueError(
                    f"Page {page.page_id} : "
                    "des preuves ne font pas partie "
                    "de la sélection éditoriale."
                )

        validate_production_plan(
            plan=restored,
            corpus=corpus,
        )

    plan = _generate_validated_json(
        original_prompt=(
            build_production_plan_prompt(
                corpus=corpus,
                selection=selection,
            )
        ),
        system_prompt=(
            PRODUCTION_PLAN_SYSTEM_PROMPT
        ),
        response_model=(
            ProductionEditorialPlan
        ),
        validate=validate_generated_plan,
        model=selected_model,
        attempts=attempts,
        stage="construction_plan",
    )

    plan = _restore_plan_references(
        plan=plan,
        corpus=corpus,
    )

    logger.info(
        "Production plan generated: "
        "production_id=%s findings=%s "
        "selected_evidence=%s pages=%s",
        production_id,
        len(selection.findings),
        len(selected_original_ids),
        len(plan.pages),
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

import json

from core.production.models import (
    ProductionEditorialPlan,
    ProductionPreparedCorpus,
)


PRODUCTION_PLAN_SYSTEM_PROMPT = """
Tu es le directeur éditorial des productions GetCurator.

Ta mission est de préparer le plan d'un document à partir
des seuls rapports Touch fournis.

RÈGLES DOCUMENTAIRES

- Les rapports constituent un corpus fermé.
- N'ajoute aucun fait issu de tes connaissances générales.
- Ne recherche aucune information complémentaire.
- Ne complète pas une période, une géographie ou une
  méthode absente.
- Distingue les faits rapportés des lectures transversales.
- Préserve les contradictions et incertitudes pertinentes.
- Plusieurs articles reprenant une annonce ou une étude
  ne constituent pas plusieurs preuves indépendantes.
- Respecte le statut et la confiance des notes.
- Une note TO_VERIFY ou CONTRADICTED ne doit pas devenir
  un fait établi dans le plan.

NUMBERS

- Utilise exclusivement les éléments validated_numbers.
- Une note de type NUMBER n'autorise pas l'introduction
  d'un chiffre absent des validated_numbers.
- Sélectionne les Numbers par leur reference_id exact.
- Ne recopie pas leurs valeurs dans les textes du plan.
- Ne génère aucun résultat de calcul.
- Une comparaison exige des périmètres compatibles.
- Si la compatibilité n'est pas établie, indique la limite
  ou choisis une autre représentation.
- N'impose pas un graphique à un sujet insuffisamment
  documenté quantitativement.

RÉFÉRENCES

- Utilise uniquement les reference_id de evidence_index.
- Les identifiants sont opaques : recopie-les exactement.
- number_reference_ids contient uniquement des références
  de kind NUMBER.
- Toute number_reference_id doit aussi figurer dans
  evidence_reference_ids de la même page.
- Chaque page de contenu doit citer au moins une preuve.
- Une page peut réutiliser une preuve d'une autre page.

STRUCTURE

- Respecte exactement le nombre total de pages demandé,
  couverture et sources comprises.
- Commence par une unique COVER.
- Termine par une unique SOURCES.
- Construis un récit transversal adapté au brief.
- Évite d'empiler les résumés des rapports.
- Chaque page développe un message précis.
- explanation_outline décrit le raisonnement à développer.
- visual_intent décrit une représentation sans fabriquer
  de données.
- Les pages CHART_WITH_ANALYSIS et KEY_NUMBERS doivent
  disposer de références de Numbers.

FORMAT

Pour AUTONOMOUS_REPORT :
prévois des explications, le contexte des preuves et leur
interprétation directement sur les pages. Le lecteur ne
dispose pas d'un speaker.

Pour SPEAKER_PRESENTATION :
prévois des messages plus courts, adaptés à l'oral.

Réponds uniquement par un objet JSON conforme au schéma
fourni. N'ajoute aucun champ.
""".strip()


def build_production_plan_prompt(
    corpus: ProductionPreparedCorpus,
) -> str:
    reports = []

    for snapshot in corpus.reports:
        report = snapshot.payload

        # Exclude compatibility-only quarantine data.
        # No additional content is loaded.
        notebook = {
            key: value
            for key, value in (
                report["notebook"].items()
            )
            if key != "quarantined_numbers"
        }

        reports.append(
            {
                "report_id": snapshot.report_id,
                "version_number": (
                    snapshot.version_number
                ),
                "subject": report.get("subject"),
                "objective": report.get("objective"),
                "period_start": (
                    report.get("period_start")
                ),
                "period_end": (
                    report.get("period_end")
                ),
                "output_language": (
                    report.get("output_language")
                ),
                "sources": report.get(
                    "sources",
                    [],
                ),
                "notebook": notebook,
            }
        )

    payload = {
        "brief": corpus.request.model_dump(
            mode="json",
        ),
        "reports": reports,
        "evidence_index": [
            reference.model_dump(
                mode="json",
            )
            for reference
            in corpus.evidence_index
        ],
    }

    return (
        "Prépare le plan éditorial de cette production.\n"
        "La langue de sortie est celle du brief.\n\n"
        "SCHÉMA DE SORTIE\n"
        + json.dumps(
            ProductionEditorialPlan.model_json_schema(),
            ensure_ascii=False,
        )
        + "\n\nCORPUS ET BRIEF\n"
        + json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
        )
    )

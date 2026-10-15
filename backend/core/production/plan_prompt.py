import json

from core.production.models import (
    ProductionEditorialPlan,
    ProductionPreparedCorpus,
)


PRODUCTION_PLAN_SYSTEM_PROMPT = """
Tu es le directeur éditorial des productions GetCurator.

Prépare un plan à partir du seul corpus fourni.
Le corpus est fermé : aucun enrichissement extérieur.

PREUVES

- Chaque preuve possède une référence simple : E00001,
  E00002, etc.
- Utilise exclusivement ces références dans
  evidence_reference_ids et number_reference_ids.
- N'utilise jamais les UUID ou identifiants internes
  présents dans les données des preuves.
- Les références sont communes à toutes les pages.
- Une preuve peut être utilisée sur plusieurs pages.
- Chaque page de contenu doit être étayée.

FIDÉLITÉ

- N'ajoute aucun fait extérieur.
- Ne complète pas une période, une zone ou une méthode
  absente.
- Préserve les limites et contradictions pertinentes.
- Respecte le statut et la confiance des notes.
- Une note TO_VERIFY ou CONTRADICTED ne devient pas
  un fait établi.
- Distingue faits rapportés et lectures transversales.
- Plusieurs reprises d'une étude ne constituent pas
  plusieurs preuves indépendantes.

NUMBERS

- Utilise uniquement les preuves de kind NUMBER pour
  sélectionner les chiffres.
- Une note contenant un chiffre ne remplace pas un
  Number sélectionné.
- number_reference_ids contient uniquement des
  références de kind NUMBER.
- Chaque référence de number_reference_ids doit aussi
  figurer dans evidence_reference_ids.
- Toute preuve NUMBER citée dans evidence_reference_ids
  doit aussi figurer dans number_reference_ids.
- Ne recopie pas les valeurs dans les textes du plan.
- Ne génère aucun résultat de calcul.
- Décris seulement la représentation envisagée.
- Ne propose pas de comparaison sans périmètres
  compatibles ; signale les informations manquantes.
- N'impose pas de graphique si les preuves ne le
  permettent pas.

LONGUEUR

- Si target_page_count est un entier, respecte exactement
  ce nombre total, couverture et sources comprises.
- Si target_page_count est null, choisis la longueur
  nécessaire entre 4 et 40 pages.
- En automatique, évite remplissage et répétitions.
- Explique brièvement le choix de longueur dans
  editorial_angle.

STRUCTURE

- Une unique COVER en première page.
- Une unique SOURCES en dernière page.
- Un récit transversal adapté à la question et au public.
- Un message précis par page.
- explanation_outline décrit le raisonnement à développer.
- visual_intent décrit la représentation envisagée.
- CHART_WITH_ANALYSIS et KEY_NUMBERS nécessitent au
  moins une preuve NUMBER.

  CONSTRUCTION DU RAPPORT

- Construis une démonstration, pas un catalogue de sujets.
- Pour chaque page d'analyse, formule un titre exprimant
  un constat précis soutenu par les preuves sélectionnées.
- Évite les formulations génériques comme "innovations",
  "tendances futures", "rester compétitif" ou "s'adapter".
- Une annonce de fonctionnalité ou de partenariat ne
  démontre pas un effet sur l'engagement, les ventes
  ou la performance.
- Ne prévois pas deux pages développant le même constat.
- La synthèse exécutive doit annoncer les enseignements
  précis du rapport, pas décrire son sommaire.
- Les implications doivent découler des constats,
  avec une question ou une décision concrète.
- Sélectionne les seules preuves nécessaires à chaque
  page. N'attache pas tout le corpus à la synthèse,
  aux implications ou aux sources.
- La page SOURCES peut décrire la bibliographie sans
  référencer l'ensemble des notes.

EXPLOITATION DES NUMBERS

- Examine toutes les preuves NUMBER avant de choisir
  les pages.
- Identifie celles qui éclairent un constat, une
  comparaison, une évolution, un cas ou une tension.
- Intègre les Numbers aux analyses auxquelles ils
  contribuent ; ne les cantonne pas à une page
  "chiffres clés".
- La synthèse peut sélectionner les Numbers essentiels.
- Les études de cas et les analyses de plateforme
  doivent mobiliser les Numbers pertinents disponibles.
- Ne fixe pas de quota : un chiffre sans contribution
  au raisonnement doit rester inutilisé.
- Ne mélange pas taux, points de pourcentage, montants,
  stocks et indices dans une même série graphique.
- Décris explicitement les indicateurs comparés et
  les conditions de leur comparaison.
- Lorsque les données sont hétérogènes, préfère des
  indicateurs séparés et commentés.

FORMAT

Pour AUTONOMOUS_REPORT, prévois contexte, explications et
interprétation directement sur les pages.

Pour SPEAKER_PRESENTATION, prévois des messages plus
courts adaptés à l'oral.

Respecte la langue du brief.
Réponds uniquement par un objet JSON conforme au schéma.
""".strip()


def build_plan_evidence_aliases(
    corpus: ProductionPreparedCorpus,
) -> dict[str, str]:
    """
    Maps short LLM aliases to the original references.
    Original references remain unchanged in storage.
    """
    return {
        f"E{index:05d}": reference.reference_id
        for index, reference in enumerate(
            corpus.evidence_index,
            start=1,
        )
    }


def build_production_plan_prompt(
    corpus: ProductionPreparedCorpus,
) -> str:
    aliases = build_plan_evidence_aliases(
        corpus
    )

    original_to_alias = {
        original: alias
        for alias, original in aliases.items()
    }

    collections = {
        "NOTE": ("notes", "note_id"),
        "EVENT": ("events", "event_id"),
        "NUMBER": (
            "validated_numbers",
            "number_id",
        ),
        "SECTION": (
            "sections",
            "section_id",
        ),
        "SUMMARY": (
            "executive_summary",
            "summary_id",
        ),
        "CROSS_READING": (
            "cross_readings",
            "reading_id",
        ),
    }

    reports = []
    evidence_data = {}

    for snapshot in corpus.reports:
        report = snapshot.payload
        notebook = report["notebook"]

        reports.append(
            {
                "report_id": snapshot.report_id,
                "version_number": (
                    snapshot.version_number
                ),
                "subject": report.get("subject"),
                "objective": report.get("objective"),
                "period_start": report.get(
                    "period_start"
                ),
                "period_end": report.get(
                    "period_end"
                ),
                "corpus_summary": notebook.get(
                    "corpus_summary",
                    "",
                ),
                "corpus_strengths": notebook.get(
                    "corpus_strengths",
                    [],
                ),
                "corpus_limits": notebook.get(
                    "corpus_limits",
                    [],
                ),
                "contradictions": notebook.get(
                    "contradictions",
                    [],
                ),
                "timeline": notebook.get(
                    "timeline",
                    [],
                ),
                "dimensions": notebook.get(
                    "dimensions",
                    [],
                ),
                "sources": report.get(
                    "sources",
                    [],
                ),
            }
        )

        for kind, (
            collection_name,
            id_field,
        ) in collections.items():
            for item in notebook.get(
                collection_name,
                [],
            ):
                key = (
                    snapshot.report_id,
                    snapshot.version_number,
                    kind,
                    item[id_field],
                )

                evidence_data[key] = item

    catalog = []

    for reference in corpus.evidence_index:
        key = (
            reference.report_id,
            reference.report_version,
            reference.kind,
            reference.local_id,
        )

        if key not in evidence_data:
            raise ValueError(
                "Une preuve du socle "
                "est introuvable : "
                f"{reference.local_id}."
            )

        catalog.append(
            {
                "reference_id": (
                    original_to_alias[
                        reference.reference_id
                    ]
                ),
                "kind": reference.kind,
                "report_id": reference.report_id,
                "report_version": (
                    reference.report_version
                ),
                "data": evidence_data[key],
            }
        )

    payload = {
        "brief": corpus.request.model_dump(
            mode="json",
        ),
        "reports": reports,
        "evidence_catalog": catalog,
    }

    return (
        "Construis le plan de production.\n\n"
        "SCHÉMA DE SORTIE\n"
        + json.dumps(
            ProductionEditorialPlan.model_json_schema(),
            ensure_ascii=False,
        )
        + "\n\nBRIEF ET CORPUS\n"
        + json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
        )
    )

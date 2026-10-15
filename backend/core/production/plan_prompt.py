import json

from core.production.models import (
    ProductionEditorialPlan,
    ProductionEditorialSelection,
    ProductionPreparedCorpus,
)


COMMON_RULES = """
Tu es le directeur éditorial des productions GetCurator.

Travaille exclusivement à partir des rapports sauvegardés
fournis. Aucun enrichissement extérieur.

FIDÉLITÉ

- Ne complète aucune période, zone, population ou méthode
  manquante.
- Une annonce ne démontre pas un effet sur les ventes,
  l'engagement ou la performance.
- Distingue observation, déclaration d'un acteur et
  interprétation éditoriale.
- Préserve les incertitudes et contradictions.
- Une note TO_VERIFY ou CONTRADICTED ne devient pas
  un fait établi.
- Plusieurs reprises d'une étude ne constituent pas
  plusieurs preuves indépendantes.
- La période du rapport n'est pas nécessairement
  la période des données qu'il contient.

RÉFÉRENCES

- Utilise uniquement les reference_id E00001, etc.
- Les identifiants internes des objets servent à comprendre
  leurs relations ; ne les utilise pas comme références
  dans la sortie.
- Les références sont propres au rapport et à sa version.
- Sélectionne seulement les preuves qui soutiennent
  directement le message proposé.

CHIFFRES

- Seules les preuves de kind NUMBER autorisent
  l'utilisation d'une valeur numérique factuelle.
- Tu peux reproduire leurs valeurs exactes dans les textes,
  avec leur unité et leur contexte.
- N'utilise pas comme chiffre établi une valeur présente
  uniquement dans une note ou une section.
- Ne produis aucun calcul dérivé à cette étape.
- Ne confonds pas pourcentages et points de pourcentage.
- Ne compare pas des indicateurs dont les périmètres
  ne sont pas compatibles.
- Des indicateurs hétérogènes peuvent être commentés
  séparément, sans les transformer en série comparable.
- Aucun quota de chiffres : leur utilité fait la sélection.

Respecte la langue du brief.
Réponds uniquement par un objet JSON conforme au schéma.
""".strip()


PRODUCTION_SELECTION_SYSTEM_PROMPT = (
    COMMON_RULES
    + """

MISSION : SÉLECTION ÉDITORIALE

Tu ne construis pas encore les pages.

Lis les rapports en conservant les liens entre leurs
sections, notes, événements, chiffres et sources.

1. Examine tous les NUMBER.
2. Identifie les constats utiles au brief et au public.
3. Pour chaque constat, formule :
   - un message précis ;
   - son intérêt pour le lecteur ;
   - les seules preuves nécessaires ;
   - les limites à préserver.
4. Mentionne les exclusions significatives :
   chiffres hors sujet, périmètres incompatibles,
   données ambiguës ou sujets secondaires.

Construis une démonstration transversale.
Ne cherche pas à représenter chaque sujet du corpus.

Un constat peut réunir plusieurs rapports.
Plusieurs constats peuvent traiter un même acteur
s'ils expliquent des mécanismes distincts.

N'associe jamais les chiffres d'un acteur à un sujet
sans rapport simplement parce qu'ils sont disponibles.

Ne sélectionne pas une section entière lorsque ses notes
ou ses chiffres suffisent à étayer le constat.

Les titres comme "Innovations technologiques" ou
"Tendances du marché" ne constituent pas des constats.

Chaque evidence_reference_ids contient les références
utiles, y compris les NUMBER pertinents.
"""
)


PRODUCTION_PLAN_SYSTEM_PROMPT = (
    COMMON_RULES
    + """

MISSION : CONSTRUCTION DU PLAN

Une sélection éditoriale et les preuves correspondantes
sont fournies. Organise-les en un rapport cohérent.

- Tu peux écarter un constat secondaire.
- Tu peux réunir ou répartir les constats selon le récit.
- N'ajoute aucune référence absente des preuves fournies.
- Un message précis par page.
- Le titre et key_message doivent exprimer l'enseignement,
  avec une valeur exacte lorsqu'elle est utile.
- explanation_outline décrit les explications concrètes
  que le lecteur devra trouver sur la page.
- Évite les formulations "Présentation de", "Discussion
  sur", "rester compétitif" et les recommandations vagues.
- La synthèse annonce les enseignements du rapport.
- Les implications proposent des questions ou décisions
  concrètes qui découlent des constats.
- Évite les répétitions et les pages de remplissage.

PREUVES PAR PAGE

- Chaque page autre que COVER et SOURCES doit contenir
  au moins une référence dans evidence_reference_ids.
- Cette obligation concerne aussi EXECUTIVE_SUMMARY
  et IMPLICATIONS.
- Pour IMPLICATIONS, référence les faits précis dont
  découle chaque question ou décision proposée.
- Une recommandation est une interprétation :
  les références étayent ses prémisses, elles ne prouvent
  pas que son résultat futur est garanti.
- Tu peux réutiliser les références pertinentes des pages
  d'analyse précédentes.
- Ne rattache pas toutes les preuves par défaut.
- Si aucune preuve fournie ne justifie une implication,
  supprime cette implication.
- Avant de répondre, vérifie ces règles pour chaque page.

NUMBERS ET VISUELS

- number_reference_ids contient exactement les références
  de kind NUMBER présentes dans evidence_reference_ids.
- Un chiffre doit soutenir le message de sa page.
- CHART_WITH_ANALYSIS et KEY_NUMBERS nécessitent
  au moins un NUMBER.
- visual_intent précise les indicateurs, unités,
  périmètres et limites de la représentation.
- Un tableau ou des indicateurs séparés peuvent être
  préférables à un graphique.
- N'invente pas de série, de base ou de comparaison.

STRUCTURE ET LONGUEUR

- Une seule COVER, en première page.
- Une seule SOURCES, en dernière page.
- Si target_page_count est un entier, respecte exactement
  ce total, couverture et sources comprises.
- Sinon, choisis entre 4 et 40 pages selon la matière.
- Justifie brièvement la longueur dans editorial_angle.
- COVER et SOURCES peuvent avoir des références vides.
- SOURCES décrit la bibliographie et les limites ;
  ne lui rattache pas toutes les preuves.

FORMAT

Pour AUTONOMOUS_REPORT, les pages doivent porter
leur contexte, leurs explications et leur interprétation.

Pour SPEAKER_PRESENTATION, les messages sont plus courts
et adaptés à un commentaire oral.
"""
)


def build_plan_evidence_aliases(
    corpus: ProductionPreparedCorpus,
) -> dict[str, str]:
    return {
        f"E{index:05d}": reference.reference_id
        for index, reference in enumerate(
            corpus.evidence_index,
            start=1,
        )
    }


def _build_report_payload(
    corpus: ProductionPreparedCorpus,
    allowed_aliases: set[str] | None = None,
) -> list[dict]:
    aliases = build_plan_evidence_aliases(
        corpus
    )

    reference_aliases = {
        (
            reference.report_id,
            reference.report_version,
            reference.kind,
            reference.local_id,
        ): alias
        for alias, reference in zip(
            aliases,
            corpus.evidence_index,
        )
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
    found_aliases = set()

    for snapshot in corpus.reports:
        report = snapshot.payload
        notebook = report["notebook"]

        groups = {}

        for kind, (
            collection_name,
            id_field,
        ) in collections.items():
            items = []

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

                alias = reference_aliases.get(
                    key
                )

                if alias is None:
                    raise ValueError(
                        "Une preuve du rapport "
                        "est absente de l'index : "
                        f"{key}."
                    )

                found_aliases.add(alias)

                if (
                    allowed_aliases is not None
                    and alias not in allowed_aliases
                ):
                    continue

                items.append({
                    "reference_id": alias,
                    "kind": kind,
                    "data": item,
                })

            groups[collection_name] = items

        reports.append({
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
            "sources": report.get(
                "sources",
                [],
            ),
            # Full editorial context is supplied during
            # selection. Planning receives selected evidence.
            "context": (
                {
                    key: notebook.get(key)
                    for key in (
                        "corpus_summary",
                        "corpus_strengths",
                        "corpus_limits",
                        "contradictions",
                        "timeline",
                        "dimensions",
                    )
                }
                if allowed_aliases is None
                else {}
            ),
            "evidence": groups,
        })

    missing = set(aliases) - found_aliases

    if missing:
        raise ValueError(
            "Des preuves de l'index sont "
            "introuvables dans les rapports : "
            + ", ".join(sorted(missing))
        )

    return reports


def _serialize_prompt(
    instruction: str,
    schema: dict,
    payload: dict,
) -> str:
    return (
        instruction
        + "\n\nSCHÉMA DE SORTIE\n"
        + json.dumps(
            schema,
            ensure_ascii=False,
        )
        + "\n\nDONNÉES\n"
        + json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
        )
    )


def build_production_selection_prompt(
    corpus: ProductionPreparedCorpus,
) -> str:
    return _serialize_prompt(
        instruction=(
            "Sélectionne les enseignements "
            "à développer dans la production."
        ),
        schema=(
            ProductionEditorialSelection
            .model_json_schema()
        ),
        payload={
            "brief": corpus.request.model_dump(
                mode="json",
            ),
            "reports": _build_report_payload(
                corpus
            ),
        },
    )


def build_production_plan_prompt(
    corpus: ProductionPreparedCorpus,
    selection: ProductionEditorialSelection,
) -> str:
    selected_aliases = {
        reference_id
        for finding in selection.findings
        for reference_id
        in finding.evidence_reference_ids
    }

    return _serialize_prompt(
        instruction=(
            "Construis le plan à partir "
            "de la sélection éditoriale."
        ),
        schema=(
            ProductionEditorialPlan
            .model_json_schema()
        ),
        payload={
            "brief": corpus.request.model_dump(
                mode="json",
            ),
            "editorial_selection": (
                selection.model_dump(
                    mode="json",
                )
            ),
            "reports": _build_report_payload(
                corpus,
                allowed_aliases=(
                    selected_aliases
                ),
            ),
        },
    )

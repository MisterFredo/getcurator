"""A fixed monthly mandate needs no separate generative planning round."""
import copy

AUTOMATIC_FRAMING = """
MONTHLY USER — CADRAGE AUTOMATIQUE
Construis directement le rapport final à partir du mandat et des preuves
figées. Le sujet, la période inclusive, la langue, la couverture et le mode
de comparaison sont dans le brief. Dérive les thèmes et leur ordre des faits
réellement étayés ; aucun thème ni nombre de sujets n'est imposé.
Prévois une couverture, une synthèse utile, les développements significatifs
et leur pertinence professionnelle, une lecture de l'évolution par rapport
à la référence disponible, puis les sources. Une comparaison impossible doit
être explicitée sans inventer d'évolution. Adapte la pagination au corpus
dans le contrat existant de 4 à 40 pages, sans remplissage.
Les sources, et non ce cadrage, sont l'autorité factuelle. Préserve les dates,
statuts et périmètres ; ne transforme pas une publication du mois en événement
du mois. Le profil définit les priorités, pas des pratiques internes établies.
Une synthèse ne fusionne pas des mécanismes distincts. N'exhibe un chiffre
que si son sens et sa fonction analytique sont explicites. Préfère l'omettre
à inventer son dénominateur ou son interprétation.
FIN_DU_PLAN
""".strip()


def compact_brief(brief):
    result = copy.deepcopy(brief)
    for key in ("report_ids", "digest_ids", "watch_reports", "target_page_count"):
        if not result.get(key):
            result.pop(key, None)
    monthly = result.get("monthly_user") or {}
    for key in ("user_id", "reference_production_id", "reference_document_artifact_id",
                "empty_current_digest_ids", "profile_source_hash", "automatic_document_attempts"):
        monthly.pop(key, None)
    for field in ("current_coverage", "previous_coverage"):
        coverage = monthly.get(field) or {}
        coverage.pop("digest_ids", None)
        # The count/span and coverage warning remain. Enumerating every absent
        # day is administrative noise, not evidence of market evolution.
        coverage.pop("missing_days", None)
    return result


def generation_payload(corpus, reviewed_plan):
    reports = []
    for snapshot in corpus.reports:
        report = copy.deepcopy(snapshot.payload)
        if report.get("source_type") == "DIGEST_SUBJECT":
            # The authoritative structured profile is already in the brief.
            # Keep every content, array index, evidence field and source URL.
            for field in ("profile", "current_profile_context", "evidence_policy"):
                report.pop(field, None)
        reports.append(report)
    return {"brief": compact_brief(corpus.request.model_dump(mode="json")),
            "reviewed_plan": reviewed_plan, "saved_reports": reports}


def review_payload(payload):
    result = dict(payload)
    result["brief"] = compact_brief(payload["brief"])
    return result

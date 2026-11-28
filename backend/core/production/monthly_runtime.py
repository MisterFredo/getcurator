"""A fixed monthly mandate needs no separate generative planning round."""
import copy

AUTOMATIC_FRAMING = """
MONTHLY USER — CADRAGE AUTOMATIQUE
Construis directement le bilan mensuel à partir des sujets sélectionnés dans
les Digests, de leurs contenus sources et du mandat du destinataire. Le brief
établit la période inclusive, la langue, la couverture et le contexte précédent.
Parcours tous les sujets du mois courant, rapproche les reprises et hiérarchise
les développements distincts selon leur intérêt métier. Ne réduis pas plusieurs
changements concrets d'un même acteur à une conclusion générale répétée.
Prévois une couverture courte, une synthèse, les développements significatifs
avec leurs faits, exemples et implications, puis les sources. Les implications
peuvent être des analyses directes ou des pistes conditionnelles, pas seulement
des questions. Fais évoluer la structure selon la matière disponible : pas de
quota de sujets ni de page systématique par acteur. Respecte le contrat de 4 à
40 pages sans remplissage. Une page trop pauvre doit être regroupée ou enrichie
à partir d'un apport distinct réellement disponible.
Utilise le mois précédent lorsqu'il apporte une comparaison utile et étayée.
Une référence partielle reste un contexte limité, pas une base exhaustive.
Regroupe les réserves générales dans une courte note ; ne les répète pas après
chaque développement. Les limites locales restent visibles lorsqu'elles
changent le sens ou l'applicabilité d'un fait.
Les contenus sont l'autorité factuelle ; les cartes et le profil guident la
sélection. Préserve dates, acteurs, marchés, statuts et portée des chiffres.
Le mandat n'établit pas les pratiques internes du destinataire. Un rapprochement
thématique ne prouve pas une intégration et une attribution n'est pas une
preuve d'incrémentalité. N'impose ni chiffres ni graphiques décoratifs.
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
            # Keep every topic, content, array index and evidence field.
            for field in ("profile", "current_profile_context", "evidence_policy"):
                report.pop(field, None)
        reports.append(report)
    return {"brief": compact_brief(corpus.request.model_dump(mode="json")),
            "reviewed_plan": reviewed_plan, "saved_reports": reports}


def review_payload(payload):
    result = dict(payload)
    result["brief"] = compact_brief(payload["brief"])
    return result

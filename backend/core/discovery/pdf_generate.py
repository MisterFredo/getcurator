"""Generate a grounded, editable draft from one PDF Studio V3 proposal. No DB writes."""
import json
import os
from openai import OpenAI

MODEL = os.getenv("PDF_STUDIO_GENERATE_MODEL", os.getenv("PDF_STUDIO_MODEL", "gpt-4o-mini"))

def generate_article(payload: dict) -> dict:
    proposal = payload.get("proposal") or {}
    evidence = proposal.get("evidence") or []
    if not isinstance(evidence, list) or len(evidence) < 3:
        raise ValueError("Trois preuves au minimum sont nécessaires pour générer un article.")
    if len(evidence) > 50:
        raise ValueError("Maximum 50 preuves par article.")
    if not str(payload.get("document_title") or "").strip():
        raise ValueError("Le titre du document est obligatoire.")
    if not str(payload.get("source_id") or "").strip():
        raise ValueError("L'identifiant de l'éditeur est obligatoire.")
    allowed = set(proposal.get("unit_ids") or [])
    if len(allowed) < 3 or any(e.get("id") not in allowed for e in evidence):
        raise ValueError("Les preuves doivent correspondre aux unités du sujet sélectionné.")
    safe = [{"id":e.get("id"),"page":e.get("page"),"fact":e.get("fact"),
             "quote":e.get("quote"),"status":e.get("status"),"reason":e.get("reason"),
             "geography":e.get("geography"),"period":e.get("period")} for e in evidence]
    instructions = """Tu rédiges un brouillon d'article B2B en français, uniquement depuis les preuves fournies.
Retourne exclusivement un objet JSON valide avec title, excerpt, body, used_unit_ids, warnings.
Titre informatif, extrait de 2 phrases, corps de 350 à 650 mots si les preuves le permettent; sinon rédige plus court.
N'invente aucune statistique, aucun nom, aucune causalité, aucun contexte extérieur.
Chaque paragraphe factuel doit indiquer les références [U00001, p. 2] correspondantes.
Ne cite pas une preuve hors sujet pour justifier une affirmation. Les preuves NEEDS_REVIEW sont provisoires:
signale leurs limites dans warnings, ne transforme jamais leur statut en vérifié.
N'affirme jamais que la citation a été validée: EXACT_TEXT_MATCH ne prouve pas l'exactitude du fait.
Si les preuves ne permettent pas un article cohérent, retourne body vide et explique pourquoi dans warnings.
Les used_unit_ids doivent provenir exclusivement de la liste fournie."""
    response = OpenAI(timeout=120, max_retries=2).chat.completions.create(
        model=MODEL,temperature=0,response_format={"type":"json_object"},
        messages=[{"role":"system","content":instructions},
                  {"role":"user","content":json.dumps({"document_title":payload["document_title"],
                    "title":proposal.get("title"),"angle":proposal.get("angle"),
                    "scope":proposal.get("scope"),"evidence":safe},ensure_ascii=False)}])
    result=json.loads(response.choices[0].message.content or "{}")
    if not isinstance(result,dict): raise ValueError("Réponse de génération invalide")
    used=[x for x in result.get("used_unit_ids",[]) if x in allowed] if isinstance(result.get("used_unit_ids"),list) else []
    warnings=result.get("warnings") if isinstance(result.get("warnings"),list) else []
    if any(e.get("status") != "VERIFIED" for e in evidence):
        warnings.append("Certaines preuves nécessitent une vérification dans le PDF source.")
    return {"status":"DRAFT_REVIEW_REQUIRED","proposal_id":proposal.get("id"),
            "document_hash":payload.get("document_hash"),"document_title":payload["document_title"],
            "source_id":payload["source_id"],"title":str(result.get("title") or proposal.get("title") or ""),
            "excerpt":str(result.get("excerpt") or ""),"body":str(result.get("body") or ""),
            "used_unit_ids":used,"warnings":warnings,"evidence":safe,"model":MODEL}

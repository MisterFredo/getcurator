"""PDF Studio V3: classify evidence, build dossiers, propose coherent articles.
Drop-in for core/discovery/pdf_consolidate.py; same consolidate(data) API.
No DB writes. The original evidence and verification flags are preserved.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any
from openai import OpenAI

MODEL = os.getenv('PDF_STUDIO_MODEL', 'gpt-4o-mini')
BATCH_SIZE = 35
MIN_EVIDENCE = 3
THEMES = ('MARKET_GROWTH','CONSUMER_BEHAVIOR','PAYMENTS','LOGISTICS','AI_TECH','REGULATION','SUSTAINABILITY','CROSS_BORDER','MARKETPLACES','BUSINESS_DIGITALIZATION','OTHER')


def ask(client: OpenAI, instruction: str, payload: dict, model: str) -> dict:
    response = client.chat.completions.create(
        model=model, temperature=0, response_format={'type': 'json_object'},
        messages=[{'role':'system','content':instruction+'\nRéponds exclusivement en JSON valide.'},
                  {'role':'user','content':json.dumps(payload,ensure_ascii=False)}],
    )
    result = json.loads(response.choices[0].message.content or '{}')
    if not isinstance(result, dict):
        raise ValueError('Réponse JSON invalide')
    return result


def prepare(data: dict) -> list[dict]:
    result = []
    for idx, u in enumerate(data.get('units', []), 1):
        if not isinstance(u, dict) or u.get('status') == 'REJECTED' or not str(u.get('fact') or '').strip():
            continue
        result.append({'id':f'U{idx:05d}','page':u.get('page'),'fact':u['fact'],
                       'quote':u.get('quote',''),'kind':u.get('kind'),
                       'geography':u.get('geography'),'period':u.get('period'),
                       'status':u.get('status','NEEDS_REVIEW'),
                       'reason':u.get('reason'),'match_score':u.get('match_score')})
    return result


def normalize(value: Any) -> str:
    value = unicodedata.normalize('NFKD',str(value or '').strip().lower())
    return re.sub(r'[^a-z0-9]+',' ', ''.join(c for c in value if not unicodedata.combining(c))).strip()


CLASSIFY = '''Tu classes des unités documentaires indépendamment de toute rédaction.
Pour CHAQUE id fourni, retourne exactement un objet {"id":"...","theme":"...","scope":"...","subtopic":"..."}.
Theme doit être une valeur de allowed_themes. Scope = pays normalisé en français, ou "Europe" pour une donnée véritablement européenne; respecte strictement le champ geography, n'invente pas une portée européenne à une donnée nationale.
Subtopic = objet précis de la preuve (par ex. "BNPL", "frais de cartes", "livraison en consigne"), 2-5 mots; ne pas employer "tendances" ou "analyse".
Ne mélange jamais deux thèmes sans preuve. Une unité doit avoir une seule affectation primaire.
Format JSON: {"assignments":[...]}'''

EDITOR = '''Tu es rédacteur en chef d'un média B2B spécialisé. Tu reçois UN dossier thématique contenant des preuves, jamais des articles préfabriqués.
Propose au maximum 3 articles DISTINCTS, chacun avec un angle informatif, précis, réellement démontré par les preuves.
Un article nécessite AU MOINS 3 preuves pertinentes et cohérentes, pas des unités choisies pour atteindre un quota.
Si le dossier n'offre pas un angle solide, retourne une liste vide. Un dossier n'est pas automatiquement un article.
Ne transforme pas des observations sans lien en un article artificiel. Tu peux réutiliser une preuve dans deux angles seulement si elle est directement pertinente aux deux.
Ne crée pas d'affirmations nouvelles, ni de conclusions causales non étayées. Tous les titres, angles et justifications doivent être en français.
Pour chaque article, sélectionne uniquement les unit_ids qui étayent DIRECTEMENT son angle; les preuves hors sujet doivent rester hors de l'article.
Format JSON: {"proposals":[{"title":"...","angle":"...","scope":"...","editorial_rationale":"...","unit_ids":["..."]}]}'''


def _ids(raw: Any, allowed: set[str]) -> list[str]:
    if not isinstance(raw,list): return []
    return list(dict.fromkeys(x for x in raw if isinstance(x,str) and x in allowed))


def consolidate(data: dict[str,Any], model: str = MODEL) -> dict[str,Any]:
    units = prepare(data)
    if not units: raise ValueError('Aucune unité exploitable')
    by_id = {u['id']:u for u in units}
    client = OpenAI(timeout=120,max_retries=2)
    assignments = {}
    # Step 1: every unit gets a thematic classification, independently of editorial proposals.
    for start in range(0,len(units),BATCH_SIZE):
        batch = units[start:start+BATCH_SIZE]
        result = ask(client,CLASSIFY,{'allowed_themes':THEMES,'units':[
            {k:u.get(k) for k in ('id','fact','geography','kind','period')} for u in batch]},model)
        allowed = {u['id'] for u in batch}
        for a in result.get('assignments',[]):
            if not isinstance(a,dict) or a.get('id') not in allowed: continue
            theme = a.get('theme') if a.get('theme') in THEMES else 'OTHER'
            u = by_id[a['id']]
            # Source geography takes precedence: model cannot silently reassign Ireland to Luxembourg.
            scope = str(u.get('geography') or a.get('scope') or 'Non précisé').strip()
            assignments[a['id']] = {'theme':theme,'scope':scope,'subtopic':str(a.get('subtopic') or '').strip()}
        for u in batch:
            assignments.setdefault(u['id'],{'theme':'OTHER','scope':str(u.get('geography') or 'Non précisé'),'subtopic':''})

    # Step 2: thematic dossiers. Normalize language variants of geography.
    geo_aliases = {'eu 27':'Europe','europe':'Europe','ireland':'Irlande','belgium':'Belgique',
                   'germany':'Allemagne','france':'France','netherlands':'Pays-Bas','pays bas':'Pays-Bas',
                   'denmark':'Danemark','sweden':'Suède','norway':'Norvège','poland':'Pologne',
                   'finland':'Finlande','austria':'Autriche','spain':'Espagne','italy':'Italie',
                   'luxembourg':'Luxembourg','estonia':'Estonie','lithuania':'Lituanie'}
    grouped = defaultdict(list)
    for u in units:
        a = assignments[u['id']]
        scope = geo_aliases.get(normalize(a['scope']),a['scope'])
        grouped[(a['theme'],scope)].append(u)
    dossiers = []
    for index,((theme,scope),members) in enumerate(sorted(grouped.items()),1):
        dossiers.append({'id':f'D{index:04d}','theme':theme,'scope':scope,
                         'unit_ids':[u['id'] for u in members], 'unit_count':len(members),
                         'subtopics':dict(Counter(assignments[u['id']]['subtopic'] for u in members if assignments[u['id']]['subtopic']))})

    # Step 3: editorial selection on complete coherent dossiers (chunk large dossiers).
    proposals = []
    for dossier in dossiers:
        members = [by_id[i] for i in dossier['unit_ids']]
        if len(members) < MIN_EVIDENCE: continue
        for start in range(0,len(members),45):
            batch = members[start:start+45]
            if len(batch) < MIN_EVIDENCE: continue
            result = ask(client,EDITOR,{'dossier':{'theme':dossier['theme'],'scope':dossier['scope']},
                 'units':[{k:u.get(k) for k in ('id','fact','kind','period','geography','status')} for u in batch]},model)
            allowed = {u['id'] for u in batch}
            for p in result.get('proposals',[]):
                if not isinstance(p,dict): continue
                ids = _ids(p.get('unit_ids'),allowed)
                if len(ids) < MIN_EVIDENCE: continue
                title = str(p.get('title') or '').strip()
                if not title: continue
                proposals.append({'title':title,'angle':str(p.get('angle') or '').strip(),
                    'scope':dossier['scope'],'editorial_rationale':str(p.get('editorial_rationale') or '').strip(),
                    'unit_ids':ids,'dossier_id':dossier['id']})

    # Merge exact duplicate titles in same dossier; preserve evidence.
    merged = {}
    for p in proposals:
        key = (p['dossier_id'],normalize(p['title']))
        if key in merged:
            merged[key]['unit_ids'] = list(dict.fromkeys(merged[key]['unit_ids']+p['unit_ids']))
        else: merged[key] = p
    final = []
    used = set()
    for idx,p in enumerate(merged.values(),1):
        evidence = [by_id[i] for i in p['unit_ids']]
        used.update(p['unit_ids'])
        final.append({**p,'id':f'A{idx:04d}',
            'pages':sorted({u['page'] for u in evidence if isinstance(u['page'],int)}),
            'evidence_count':len(evidence),
            'exact_quote_count':sum(u['status']=='VERIFIED' for u in evidence),
            'review_count':sum(u['status']!='VERIFIED' for u in evidence),
            'editorial_status':'REVIEW_REQUIRED','evidence':evidence})
    uncovered = [u for u in units if u['id'] not in used]
    return {'document_hash':data.get('document_hash'),'document_title':data.get('document_title'),
        'source_id':data.get('source_id'),'model':model,'version':'3.0',
        'summary':{'input_units':len(units),'dossier_count':len(dossiers),
            'article_proposals':len(final),'covered_units':len(used),
            'uncovered_units':len(uncovered),'coverage_percent':round(100*len(used)/len(units),1),
            'unit_statuses':dict(Counter(u['status'] for u in units))},
        'dossiers':dossiers,'assignments':assignments,'proposals':final,
        'uncovered_evidence':uncovered,'singletons':[],
        'note':'Dossiers documentaires et propositions non validées. Aucune génération ni écriture en base.'}

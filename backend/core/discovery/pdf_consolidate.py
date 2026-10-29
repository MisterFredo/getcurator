"""PDF Studio: turn extracted evidence units into editorial article proposals.

CLI: python pdf_consolidate.py input.json --output proposals.json
Requires OPENAI_API_KEY and openai>=2.0.0. Does not write to BigQuery.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any
from openai import OpenAI

MODEL = os.getenv('PDF_STUDIO_MODEL', 'gpt-4o-mini')
CHUNK = 65


def ask(client: OpenAI, system: str, payload: dict[str, Any], model: str) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model, temperature=0, response_format={'type': 'json_object'},
        messages=[{'role': 'system', 'content': system + '\nRéponds exclusivement avec un objet JSON valide.'}, {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}],
    )
    result = json.loads(response.choices[0].message.content or '{}')
    if not isinstance(result, dict):
        raise ValueError('Invalid JSON object from model')
    return result


def prepare(data: dict[str, Any]) -> list[dict[str, Any]]:
    units = []
    for i, item in enumerate(data.get('units', [])):
        if not isinstance(item, dict) or item.get('status') == 'REJECTED' or not item.get('fact'):
            continue
        units.append({
            'id': f'U{i+1:05d}', 'page': item.get('page'),
            'fact': item['fact'], 'quote': item.get('quote', ''),
            'kind': item.get('kind'), 'geography': item.get('geography'),
            'period': item.get('period'), 'status': item.get('status'),
            'reason': item.get('reason'), 'match_score': item.get('match_score'),
        })
    return units


def normalize_proposals(raw: Any, allowed: set[str], prefix: str) -> list[dict[str, Any]]:
    output = []
    if not isinstance(raw, list):
        return output
    for index, p in enumerate(raw):
        if not isinstance(p, dict):
            continue
        ids = list(dict.fromkeys(x for x in p.get('unit_ids', []) if isinstance(x, str) and x in allowed))
        title = str(p.get('title') or '').strip()
        if not title or len(ids) < 2:
            continue
        output.append({
            'id': f'{prefix}{index+1:03d}', 'title': title,
            'angle': str(p.get('angle') or '').strip(),
            'unit_ids': ids, 'scope': str(p.get('scope') or '').strip(),
            'editorial_rationale': str(p.get('editorial_rationale') or '').strip(),
        })
    return output


def consolidate(data: dict[str, Any], model: str = MODEL) -> dict[str, Any]:
    units = prepare(data)
    if not units:
        raise ValueError('No usable units in extraction')
    by_id = {u['id']: u for u in units}
    client = OpenAI(timeout=120, max_retries=2)
    local: list[dict[str, Any]] = []
    # Chunk proposals are a candidate discovery stage, not the final editorial list.
    for offset in range(0, len(units), CHUNK):
        batch = units[offset:offset + CHUNK]
        payload = {'units': [{k: u[k] for k in ('id', 'page', 'fact', 'kind', 'geography', 'period', 'status')} for u in batch]}
        parsed = ask(client,
            'Tu es un rédacteur en chef B2B. Regroupe les unités en SUJETS D’ARTICLES autonomes. '
            'Ne rédige PAS les articles. Cherche des angles précis, transversaux si justifiés, et des angles pays. '
            'Ne transforme pas chaque chiffre en article. Évite les sujets génériques, les répétitions et les rapprochements artificiels. '
            'Une unité peut figurer dans plusieurs propositions si les angles sont réellement distincts. '
            'Ne cite que des unit_ids fournis. Aucun fait inventé. '
            'Retourne {"proposals":[{"title":"...","angle":"...","scope":"...",'
            '"editorial_rationale":"...","unit_ids":["U00001",...] }]} ; vise une couverture large.',
            payload, model)
        local.extend(normalize_proposals(parsed.get('proposals'), set(u['id'] for u in batch), f'L{offset//CHUNK+1:02d}-'))

    # Cross-batch editorial consolidation: group proposals into a global article list.
    # Unit IDs remain attached and are validated against the extraction.
    candidates = [{'id': p['id'], 'title': p['title'], 'angle': p['angle'],
                   'scope': p['scope'], 'unit_ids': p['unit_ids']} for p in local]
    global_result = ask(client,
        'Tu es le rédacteur en chef de GetCurator. Fusionne les propositions redondantes et '
        'propose une liste finale aussi riche que nécessaire d’ARTICLES DISTINCTS et documentés. '
        'Conserve des articles pays quand ils apportent un angle spécifique, et des articles comparatifs '
        'si les unités les étayent. Ne fusionne pas des sujets seulement parce qu’ils sont dans le même secteur. '
        'Ne crée aucun fait, ne cite que les unit_ids autorisés présents dans les propositions. '
        'Un article doit contenir au moins deux unités; préfère au moins trois preuves indépendantes. '
        'Retourne {"proposals":[{"title":"...","angle":"...","scope":"...",'
        '"editorial_rationale":"...","unit_ids":["U00001",...] }]}. '
        'Ce sont des PROPOSITIONS pour revue, jamais des articles prêts à publier.',
        {'candidates': candidates}, model)
    final = normalize_proposals(global_result.get('proposals'), set(by_id), 'A')
    used = set()
    for p in final:
        evidence = [by_id[x] for x in p['unit_ids']]
        used.update(p['unit_ids'])
        p['pages'] = sorted({u['page'] for u in evidence if isinstance(u['page'], int)})
        p['evidence_count'] = len(evidence)
        p['exact_quote_count'] = sum(u['status'] == 'VERIFIED' for u in evidence)
        p['review_count'] = sum(u['status'] != 'VERIFIED' for u in evidence)
        p['editorial_status'] = 'REVIEW_REQUIRED'  # Matching a quote never verifies the entire claim.
        p['evidence'] = evidence
    return {
        'document_hash': data.get('document_hash'), 'document_title': data.get('document_title'),
        'source_id': data.get('source_id'), 'model': model,
        'summary': {'input_units': len(units), 'local_proposals': len(local),
                    'article_proposals': len(final), 'covered_units': len(used),
                    'uncovered_units': len(units)-len(used),
                    'unit_statuses': dict(Counter(u['status'] for u in units))},
        'proposals': final,
        'uncovered_evidence': [u for u in units if u['id'] not in used],
        'note': 'No content generated or imported. Human validation of facts and citations required.',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='PDF Studio editorial consolidation')
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, default=Path('pdf-proposals.json'))
    parser.add_argument('--model', default=MODEL)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8'))
    result = consolidate(data, model=args.model)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    print(f'Saved: {args.output}')

if __name__ == '__main__':
    main()

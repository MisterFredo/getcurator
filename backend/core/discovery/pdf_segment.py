"""PDF Studio V6: document-first segmentation, no LLM, no persistence.

Segments are page-bounded *candidate* sections. Interview subtopics are hints,
not separate text excerpts: multi-column PDF reading order is not reliable.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

import fitz

def _normalize(text: str) -> str:
    return re.sub(r"[ \t]+", " ", (text or "").replace("\u00a0", " ")).strip()

def _load(data: bytes):
    if not data or len(data) > 30 * 1024 * 1024 or not data.startswith(b"%PDF"):
        raise ValueError("PDF invalide ou supérieur à 30 Mo")
    doc = fitz.open(stream=data, filetype="pdf")
    if doc.needs_pass or not 1 <= len(doc) <= 300:
        doc.close()
        raise ValueError("PDF protégé ou nombre de pages invalide")
    return doc

REGIONS = {'WESTERN EUROPE', 'NORTHERN EUROPE', 'CENTRAL EUROPE', 'EASTERN EUROPE', 'SOUTHERN EUROPE'}
COUNTRIES = {'Albania','Austria','Belgium','Bosnia and Herzegovina','Bulgaria','Croatia','Cyprus','Czech Republic','Denmark','Estonia','Finland','France','Germany','Greece','Hungary','Iceland','Ireland','Italy','Latvia','Lithuania','Luxembourg','Malta','Moldova','Montenegro','Netherlands','North Macedonia','Norway','Poland','Portugal','Romania','Serbia','Slovak Republic','Slovenia','Spain','Sweden','Switzerland','Ukraine','United Kingdom'}
HEADINGS = {'Policies and regulation':'regulation','Sustainability':'sustainability','Technology':'technology','e-Payments':'payments','e-Logistics':'logistics','Other areas related to e-commerce':'consumer_behavior'}


def _toc_from_pdf(doc) -> list[dict[str, Any]]:
    """Read explicit PDF bookmarks when available; otherwise derive boundaries from page headers.

    Page headers are validated against a stable controlled vocabulary and avoid
    unreliable extraction of the multi-column printed table of contents.
    """
    bookmarks = doc.get_toc()
    if bookmarks:
        entries = []
        for level, title, page in bookmarks:
            if 1 <= page <= len(doc) and title.strip():
                entries.append({'page':page,'title':title.strip(),'level':level,'origin':'pdf_bookmark'})
        if len(entries) >= 5:
            return entries
    entries=[{'page':1,'title':'Cover','kind':'front','region':None,'level':1,'origin':'first_page'}]
    last_key=None
    for i, page in enumerate(doc):
        text=page.get_text('text',sort=True)
        first=next((x.strip() for x in text.splitlines() if x.strip()),'')
        # Report's running header has stable 'page | title | region | country' form.
        parts=[x.strip() for x in first.split('|')]
        if len(parts)<3 or not re.match(r'^\d+$',parts[0]):
            continue
        if len(parts)>=4 and parts[-1] in COUNTRIES:
            key=('country',parts[-1],parts[-2])
        elif parts[-1].upper() in REGIONS:
            key=('region',parts[-1],None)
        elif parts[-1].lower() in {'contents','introduction','copyright'}:
            key=('front',parts[-1],None)
        else:
            key=('overview',parts[-1],None)
        if key!=last_key:
            entries.append({'page':i+1,'title':key[1],'kind':key[0], 'region':key[2], 'level':2 if key[0]=='country' else 1,'origin':'running_header'})
            last_key=key
    return entries


def segment_pdf(pdf_bytes:bytes,filename:str='document.pdf')->dict[str,Any]:
    with _load(pdf_bytes) as doc:
        entries=_toc_from_pdf(doc)
        if not entries:
            raise ValueError('Impossible de détecter le plan : segmentation manuelle requise')
        entries=sorted(entries,key=lambda e:e['page'])
        segments=[]
        for idx,entry in enumerate(entries):
            start=entry['page']
            end=(entries[idx+1]['page']-1) if idx+1<len(entries) else len(doc)
            if end<start:continue
            texts=[]
            detected=[]
            for n in range(start,end+1):
                raw=doc[n-1].get_text('text',sort=True)
                texts.append({'page':n,'text':_normalize(raw)})
                for heading,topic in HEADINGS.items():
                    if re.search(r'(?im)^\s*'+re.escape(heading)+r'\s*$',raw):
                        detected.append({'page':n,'heading':heading,'topic':topic})
            country=entry['title'] if entry.get('kind')=='country' else None
            segments.append({'id':f'S{len(segments)+1:04d}','title':entry['title'],
                'kind':entry.get('kind','bookmark'),'start_page':start,'end_page':end,
                'country_primary':country,'region':entry.get('region'),
                'subtopic_candidates':detected,'pages':texts,
                'review_status':'NEEDS_REVIEW',
                'note':'Sous-rubriques repérées mais texte non isolé : découpage fin à valider.' if detected else None})
        covered={p['page'] for s in segments for p in s['pages']}
        return {'status':'SEGMENTED_CANDIDATES','version':'6.0',
            'document':{'document_hash':hashlib.sha256(pdf_bytes).hexdigest(),'filename':filename,'page_count':len(doc)},
            'summary':{'segments':len(segments),'pages_covered':len(covered),'uncovered_pages':[i for i in range(1,len(doc)+1) if i not in covered]},
            'sections':entries,'segments':segments,
            'note':'Plan et segments par pages. Ne pas générer des articles par sous-rubrique avant validation de leurs bornes textuelles.'}

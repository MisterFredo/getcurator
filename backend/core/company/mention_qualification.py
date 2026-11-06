"""Conservative editorial extraction: no publication date/proof -> technical journal."""
from __future__ import annotations
import json
import re
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

POLICY='mention-1.0'
class Uncertain(ValueError):
    pass


def contains_alias(text, aliases):
    return any(re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',text,re.I) for alias in aliases)


def domain(value):
    value=value.strip().lower()
    host=urlsplit(value if '://' in value else 'https://'+value).hostname
    if not host or not re.fullmatch(r'[a-z0-9.-]+',host):raise ValueError('Domaine exclu invalide')
    return host.removeprefix('www.')


def excluded(url, domains):
    host=(urlsplit(url).hostname or '').lower().removeprefix('www.')
    return any(host==d or host.endswith('.'+d) for d in domains)


def google_url(url):
    host=(urlsplit(url).hostname or '').lower()
    return bool(re.fullmatch(r'(?:[a-z0-9-]+\.)?google\.[a-z.]+',host) or host=='news.google.com')


def _publication_date(values):
    parsed=[]
    for value in values:
        if not isinstance(value,str):continue
        try:
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
                stamp=datetime.combine(date.fromisoformat(value),time(),ZoneInfo('Europe/Paris'));precision='DAY'
            else:
                stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
                if stamp.tzinfo is None:continue
                precision='SOURCE_TIMESTAMP'
            parsed.append((stamp,precision))
        except ValueError:continue
    days={stamp.astimezone(ZoneInfo('Europe/Paris')).date() for stamp,_ in parsed}
    if not days:raise Uncertain('PUBLICATION_DATE_UNKNOWN')
    if len(days)>1:raise Uncertain('PUBLICATION_DATE_CONFLICT')
    return parsed[0]


def editorial_page(html, url, aliases, start, end):
    soup=BeautifulSoup(html,'html.parser')
    values=[];author=None
    meta=soup.find('meta',property='article:published_time')
    if meta and meta.get('content'):values.append(meta['content'])
    for script in soup.find_all('script',type='application/ld+json'):
        try:payload=json.loads(script.string or script.get_text())
        except (ValueError,TypeError):continue
        pending=payload if isinstance(payload,list) else [payload]
        while pending:
            item=pending.pop()
            if not isinstance(item,dict):continue
            pending.extend(item.get('@graph') or [])
            kinds=item.get('@type') or [];kinds=[kinds] if isinstance(kinds,str) else kinds
            if any(k in {'Article','NewsArticle','BlogPosting','Report','TechArticle'} for k in kinds):
                if item.get('datePublished'):values.append(item['datePublished'])
                a=item.get('author')
                if isinstance(a,dict):author=a.get('name')
                elif isinstance(a,str):author=a
    stamp,precision=_publication_date(values)
    day=stamp.astimezone(ZoneInfo('Europe/Paris')).date()
    if not date.fromisoformat(start)<=day<=date.fromisoformat(end):raise Uncertain('OUTSIDE_PUBLICATION_PERIOD')
    region=soup.find('article') or soup.select_one('[itemprop="articleBody"]') or soup.find('main')
    if not region:raise Uncertain('EDITORIAL_REGION_UNKNOWN')
    title=soup.find('h1') or soup.title
    title=title.get_text(' ',strip=True) if title else url
    for node in list(region.select('script,style,noscript,nav,header,footer,form,button,iframe,[role="dialog"],[aria-hidden="true"]')):
        if node.parent is not None:node.decompose()
    for node in list(region.find_all(True)):
        if node.parent is None:continue
        label=' '.join([str(node.get('id') or ''),*node.get('class',[])])
        if node.parent is not None and re.search(r'axeptio|didomi|onetrust|cookie[-_ ]?(?:banner|notice|modal)|cmp[-_]container',label,re.I):node.decompose()
    text=region.get_text('\n',strip=True)
    if len(text)<100:raise Uncertain('EDITORIAL_TEXT_TOO_SHORT')
    if len(text)>30000:raise Uncertain('EDITORIAL_TEXT_TOO_LONG')
    if not contains_alias(text,aliases):raise Uncertain('NO_EDITORIAL_MENTION')
    return {'title':title,'text':text,'published_at':stamp.isoformat(),'date_precision':precision,'author':author}


def validate_assessment(raw, page, aliases):
    try:r=json.loads(raw)
    except (ValueError,TypeError):raise Uncertain('INVALID_QUALIFICATION')
    if not isinstance(r,dict) or r.get('relevant') is not True:raise Uncertain('EDITORIAL_RELEVANCE_UNCERTAIN')
    quote=r.get('quote');explanation=r.get('explanation')
    if not isinstance(quote,str) or len(quote)<20 or quote not in page['text'] or not contains_alias(quote,aliases):
        raise Uncertain('QUOTE_NOT_VERIFIED')
    if not isinstance(explanation,str) or not 30<=len(explanation)<=2000:raise Uncertain('EXPLANATION_INVALID')
    return {'quote':quote,'explanation':explanation,'start':page['text'].index(quote),
            'end':page['text'].index(quote)+len(quote)}

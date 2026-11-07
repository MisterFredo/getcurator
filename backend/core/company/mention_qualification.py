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
    def __init__(self, reason, **details):
        super().__init__(reason)
        self.details=details


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


DATE_VERSION='mention-1.5'
MONTHS={'janvier':1,'février':2,'fevrier':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'août':8,'aout':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12,'decembre':12,
        'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,'july':7,'august':8,'september':9,'october':10,'november':11,'december':12}


def _date_value(value):
    value=str(value or '').strip()
    # A source timestamp without timezone proves a calendar day, not an instant.
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?',value):return value[:10]
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T.*)?',value):return value
    value=value.casefold().replace(',',' ')
    match=re.search(r'(?<!\d)(\d{1,2})\s+([a-zéûôî]+)\s+(\d{4})(?!\d)',value)
    if match and match[2] in MONTHS:
        try:return date(int(match[3]),MONTHS[match[2]],int(match[1])).isoformat()
        except ValueError:return None
    match=re.search(r'\b([a-z]+)\s+(\d{1,2})\s+(\d{4})(?!\d)',value)
    if match and match[1] in MONTHS:
        try:return date(int(match[3]),MONTHS[match[1]],int(match[2])).isoformat()
        except ValueError:return None
    return None


CONTENT_SELECTORS=('[itemprop="articleBody"]','.elementor-widget-theme-post-content',
    '.entry-content','.post-content','.article-content','.article-body','article','main')


def _clean_region(node):
    clone=BeautifulSoup(str(node),'html.parser').find()
    # Remove entire widgets/cards, not article text mentioning the word cookies.
    for child in list(clone.select('script,style,noscript,nav,header,footer,form,button,iframe,aside,[role="dialog"],[aria-hidden="true"],.elementor-posts-container,.related-posts,.related-articles')):
        if child.parent is not None:child.decompose()
    for child in list(clone.find_all(True)):
        if child.parent is None:continue
        label=' '.join([str(child.get('id') or ''),*child.get('class',[])])
        if re.search(r'didomi|onetrust|cookie[-_ ]?(?:banner|notice|modal)|cmp[-_]container|axeptio[_-](?:widget|overlay|container)',label,re.I):child.decompose()
    return clone.get_text('\n',strip=True)


def _select_region(soup):
    candidates=[];seen=set()
    for rank,selector in enumerate(CONTENT_SELECTORS):
        for node in soup.select(selector):
            if id(node) in seen:continue
            seen.add(id(node));text=_clean_region(node)
            # Explicit body selectors outrank broad wrappers, but a tiny widget
            # must not beat the actual article. Never score by company occurrence.
            strong=rank<6 and len(text)>=100
            candidates.append(((1 if strong else 0,len(text)),node,text,selector))
    if not candidates:raise Uncertain('EDITORIAL_REGION_UNKNOWN')
    _,node,text,selector=max(candidates,key=lambda item:item[0])
    return node,text,selector


def inspect_editorial(html, url, aliases, start=None, end=None):
    soup=BeautifulSoup(html,'html.parser');values=[];sources=[];author=None
    def add(value,locator):
        parsed=_date_value(value)
        if parsed:values.append(parsed);sources.append({'locator':locator,'value':str(value),'normalized':parsed})
    for node in soup.select('meta[property="article:published_time"],meta[itemprop="datePublished"],meta[name="pubdate"],meta[name="publishdate"],meta[name="datePublished"],meta[name="DC.date.issued"],meta[property="og:article:published_time"]'):
        add(node.get('content'),str(node))
    article_schema=False;reference_schema=False
    for script in soup.find_all('script',type='application/ld+json'):
        try:payload=json.loads(script.string or script.get_text())
        except (ValueError,TypeError):continue
        pending=payload if isinstance(payload,list) else [payload]
        while pending:
            item=pending.pop()
            if not isinstance(item,dict):continue
            graph=item.get('@graph');pending.extend(graph if isinstance(graph,list) else [])
            kinds=item.get('@type') or [];kinds=[kinds] if isinstance(kinds,str) else kinds
            article=any(k in {'Article','NewsArticle','BlogPosting','Report','TechArticle'} for k in kinds)
            article_schema=article_schema or article
            reference_schema=reference_schema or any(k in {'Product','SoftwareApplication','FAQPage','CollectionPage'} for k in kinds)
            if article:
                add(item.get('datePublished'),'JSONLD.datePublished')
                a=item.get('author')
                if isinstance(a,dict):author=a.get('name')
                elif isinstance(a,str):author=a
    # Known out-of-period metadata is decisive even if the reader later fails.
    if start and end and values:
        try:apply_publication_date({'date_values':values},start,end)
        except Uncertain as exc:
            if str(exc)!='PUBLICATION_DATE_UNKNOWN':raise Uncertain(str(exc),date_sources=sources)
    region,text,reader_selector=_select_region(soup)
    title_node=region.find('h1') or soup.find('h1') or soup.title
    title=title_node.get_text(' ',strip=True) if title_node else url
    date_region=region.find_parent('article') or region.find_parent('main') or region
    for node in date_region.select('[itemprop="datePublished"]'):
        add(node.get('content') or node.get('datetime') or node.get_text(' ',strip=True),'EDITORIAL.itemprop.datePublished')
    # Generic <time> can describe an event or modification. Require publication semantics.
    for node in date_region.find_all('time'):
        label=' '.join([str(node.get('class') or ''),str(node.get('itemprop') or ''),str(node.parent.get('class') or '')]).casefold()
        visible=node.parent.get_text(' ',strip=True)[:250].casefold()
        if re.search(r'updated|modified|mis[ e]à jour|modifi',label+' '+visible):continue
        if re.search(r'publish|publi[ée]|posted|datepublished',label+' '+visible):
            add(node.get('datetime') or node.get_text(' ',strip=True),'EDITORIAL.publication_time')
    # Explicit visible publication labels only: never a date guessed from arbitrary prose.
    for node in date_region.select('.published,.published-at,.publication-date,.date-published'):
        value=node.get_text(' ',strip=True)
        if not re.search(r'updated|modified|mise? à jour',value,re.I):add(value,'EDITORIAL.publication_label')
    for node in date_region.find_all(['p','span','div']):
        visible=node.get_text(' ',strip=True)
        if len(visible)<=160 and re.match(r'^(?:publié(?:e)?(?: le)?|published(?: on)?|posted(?: on)?)\s*[:：]?\s+',visible,re.I):
            if not re.search(r'updated|modified|mise? à jour',visible,re.I):add(visible,'EDITORIAL.explicit_publication_label')
    reference_path=bool(re.search(r'/(?:tag|tags|category|categories|vendors|outils-cro|docs|documentation|help|support)(?:/|$)',urlsplit(url).path,re.I))
    diagnostics={'reader_selector':reader_selector,'text_length':len(text),'date_sources':sources}
    if start and end and values:
        try:apply_publication_date({'date_values':values},start,end)
        except Uncertain as exc:
            if str(exc)!='PUBLICATION_DATE_UNKNOWN':raise Uncertain(str(exc),**diagnostics)
    if len(text)<100:raise Uncertain('EDITORIAL_TEXT_TOO_SHORT',**diagnostics)
    if len(text)>30000:raise Uncertain('EDITORIAL_TEXT_TOO_LONG',**diagnostics)
    if not contains_alias(text,aliases):raise Uncertain('NO_EDITORIAL_MENTION',**diagnostics)
    if (reference_schema or reference_path) and not article_schema:raise Uncertain('REFERENCE_PAGE_NOT_NEWS',**diagnostics)
    return {'title':title,'text':text,'author':author,'date_values':values,'date_sources':sources,
            'reader_selector':reader_selector,'text_length':len(text),'page_nature':'ARTICLE' if article_schema or region.name=='article' else 'UNDETERMINED'}


def apply_publication_date(page,start,end):
    stamp,precision=_publication_date(page['date_values'])
    day=stamp.astimezone(ZoneInfo('Europe/Paris')).date()
    if not date.fromisoformat(start)<=day<=date.fromisoformat(end):raise Uncertain('OUTSIDE_PUBLICATION_PERIOD')
    return {**page,'published_at':stamp.isoformat(),'date_precision':precision}


def editorial_page(html,url,aliases,start,end):
    return apply_publication_date(inspect_editorial(html,url,aliases,start,end),start,end)


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

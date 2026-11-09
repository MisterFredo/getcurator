"""Pure employer matching from observed Bright Data profile fields. No fuzzy decisions."""
from urllib.parse import urlsplit,unquote
import re

def company_url(value):
    if not isinstance(value,str):return None
    try:
        p=urlsplit(value.strip());host=(p.hostname or '').lower()
        if p.scheme.lower() not in ('http','https') or not (host=='linkedin.com' or host.endswith('.linkedin.com')) or p.username or p.password or p.port not in (None,80,443):return None
        match=re.fullmatch(r'/company/([^/\s?#\\]+)(?:/)?',unquote(p.path))
        return 'https://www.linkedin.com/company/'+match[1].casefold() if match else None
    except ValueError:return None

def employer(profile):
    if profile.get('error') or profile.get('error_code'):return None,'Erreur de collecte du profil'
    current=profile.get('current_company')
    if not isinstance(current,dict):return None,'Employeur actuel absent ou format non reconnu'
    name=str(current.get('name') or profile.get('current_company_name') or '').strip()
    url=company_url(current.get('link'))
    slug=str(current.get('company_id') or '').strip().casefold()
    if slug and url and url.rsplit('/',1)[-1]!=slug:return None,'Identifiants de société contradictoires'
    if not name:return None,'Nom de l’employeur actuel absent'
    # Only explicitly current experiences count. An absent end date alone is not proof.
    extra=set()
    for role in profile.get('experience') or []:
        if not isinstance(role,dict):continue
        if role.get('is_current') is True or str(role.get('end_date') or '').strip().casefold() in ('present','current','aujourd’hui',"aujourd'hui"):
            other=company_url(role.get('company_url') or role.get('url'))
            other_name=str(role.get('company') or role.get('company_name') or '').strip().casefold()
            if other and url and other!=url:extra.add(other)
            elif other_name and other_name!=name.casefold():extra.add(other_name)
    if extra:return None,'Plusieurs emplois actuels : rapprochement manuel requis'
    return {'name':name,'url':url},None

def match(observed,companies,aliases,memory,normalize,key):
    ids={c['ID_COMPANY'] for c in companies}
    urls={c['ID_COMPANY'] for c in companies if observed['url'] and company_url(c.get('LINKEDIN_URL'))==observed['url']}
    name=normalize(observed['name'])
    names={c['ID_COMPANY'] for c in companies if normalize(c.get('NAME'))==name}
    names.update(a['ID_COMPANY'] for a in aliases if a['ID_COMPANY'] in ids and normalize(a.get('ALIAS'))==name)
    names.update(m['ID_COMPANY'] for m in memory if m['ID_COMPANY'] in ids and m['COMPANY_KEY']==key(observed['name']))
    if len(urls)>1 or len(names)>1:return None,'Plusieurs sociétés correspondent'
    if urls and names and urls!=names:return None,'URL société et nom/alias pointent vers des sociétés différentes'
    candidates=urls or names
    return (next(iter(candidates)),None) if len(candidates)==1 else (None,'Société à rapprocher')

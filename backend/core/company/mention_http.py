"""Mention-only HTTP reader: public URLs, per-hop single flight, typed failures.

Failed final URLs are remembered only within a run, never as permanent exclusions.
"""
from concurrent.futures import Future
import logging
from threading import Lock
from time import perf_counter
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
from core.company.watch_http import normalize_url, url_key, _public_url, HEADERS, MAX_BYTES

logger=logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:logger.addHandler(logging.StreamHandler())
logger.propagate=False

class FetchFailure(RuntimeError):
    def __init__(self,reason,url,detail,*,reused=False):
        super().__init__(reason)
        self.reason=reason
        self.details={'resolved_url':url_key(url),'technical_detail':detail[:300],'failure_reused':reused}

class HopCache:
    """One HTTP operation per exact URL in a four-worker lot, including errors."""
    def __init__(self):self.lock=Lock();self.futures={}
    def get(self,url,producer):
        with self.lock:
            future=self.futures.get(url);owner=future is None
            if owner:future=Future();self.futures[url]=future
        if owner:
            try:future.set_result((producer(),None))
            except FetchFailure as exc:future.set_result((None,(exc.reason,dict(exc.details))))
            except BaseException as exc:future.set_exception(exc)
        value,error=future.result()
        if error:
            reason,details=error
            raise FetchFailure(reason,details['resolved_url'],details['technical_detail'],reused=not owner)
        return value


def _hop(url):
    started=perf_counter()
    try:
        _public_url(url)
        with requests.Session() as session:
            with session.get(url,headers=HEADERS,timeout=(10,25),stream=True,allow_redirects=False) as response:
                status=response.status_code
                if status in {301,302,303,307,308}:
                    location=response.headers.get('Location')
                    if not location:raise FetchFailure('TECHNICAL_REDIRECT_MISSING_LOCATION',url,'Redirection sans en-tête Location')
                    return {'redirect':normalize_url(urljoin(url,location))}
                if status>=400:raise FetchFailure(f'TECHNICAL_HTTP_{status}',url,f'HTTP {status}')
                mime=response.headers.get('Content-Type','').split(';')[0].lower().strip()
                if mime not in {'text/html','application/xhtml+xml'}:
                    raise FetchFailure('TECHNICAL_NON_HTML',url,f'Type de contenu reçu : {mime or "absent"}')
                chunks=[];size=0
                for chunk in response.iter_content(65536):
                    size+=len(chunk)
                    if size>MAX_BYTES:raise FetchFailure('TECHNICAL_HTML_SIZE_LIMIT',url,'Page HTML supérieure à 5 Mo')
                    chunks.append(chunk)
                return {'url':url,'html':str(BeautifulSoup(b''.join(chunks),'html.parser'))}
    except FetchFailure:raise
    except requests.ConnectTimeout:raise FetchFailure('TECHNICAL_CONNECT_TIMEOUT',url,'Délai de connexion dépassé') from None
    except requests.ReadTimeout:raise FetchFailure('TECHNICAL_READ_TIMEOUT',url,'Délai de lecture dépassé') from None
    except requests.exceptions.SSLError:raise FetchFailure('TECHNICAL_SSL_ERROR',url,'Échec de validation TLS') from None
    except requests.RequestException:raise FetchFailure('TECHNICAL_CONNECTION_ERROR',url,'Échec de connexion ou de lecture HTTP') from None
    except ValueError as exc:
        # These messages originate from our own URL/public-network checks.
        raise FetchFailure('TECHNICAL_URL_OR_RESPONSE_INVALID',url,str(exc)) from None
    finally:
        logger.info('[MENTIONS] HTTP hop host=%s seconds=%.2f',urlsplit(url).hostname,perf_counter()-started)


def fetch_html(url,*,prior_failures=None,memo=None):
    url=normalize_url(url);initial_url=url;visited=set();memo=memo or HopCache()
    for _ in range(6):
        if url in visited:raise FetchFailure('TECHNICAL_REDIRECT_LOOP',url,'Boucle de redirections HTTP')
        visited.add(url)
        known=(prior_failures or {}).get(url_key(url))
        if known:
            raise FetchFailure(known['reason'],url,known.get('technical_detail','Échec déjà observé dans cette collecte'),reused=True)
        page=memo.get(url,lambda:_hop(url))
        if 'redirect' not in page:return page
        url=normalize_url(page['redirect'])
    raise FetchFailure('TECHNICAL_REDIRECT_LIMIT',initial_url,'Plus de six étapes de redirection HTTP')

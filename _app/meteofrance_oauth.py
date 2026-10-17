"""Gestion d'un profil OAuth commun : préparation, aucun appel automatique au chargement."""
import os,time,json,tempfile,threading
from pathlib import Path
from datetime import datetime,timezone,timedelta
from contextlib import contextmanager
import requests

ENDPOINT='https://portail-api.meteofrance.fr/token'
LOCK=threading.Lock()

@contextmanager
def profile_lock(path):
    lockpath=Path(str(path)+'.lock')
    lockpath.parent.mkdir(parents=True,exist_ok=True)
    with LOCK,lockpath.open('a+b') as stream:
        stream.seek(0,os.SEEK_END)
        if stream.tell()==0:stream.write(b'0');stream.flush()
        deadline=time.monotonic()+5
        while True:
            try:
                stream.seek(0)
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic()>=deadline:raise RuntimeError('mf_oauth_busy') from None
                time.sleep(.05)
        try:yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)

def load(path):
    try:data=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):raise RuntimeError('mf_oauth_config_invalid') from None
    if not isinstance(data,dict):raise RuntimeError('mf_oauth_config_invalid')
    return data

def save(path,data):
    fd,temp=tempfile.mkstemp(dir=Path(path).parent,prefix='.mf-oauth-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def access_token(path,requester=None,now=None,*,force_refresh=False):
    path=Path(path)
    # Aucun jeton manuel ne déclenche une génération implicite.
    if load(path).get('auth_mode')!='oauth2':raise RuntimeError('mf_oauth_not_enabled')
    with profile_lock(path):
        config=load(path)
        if config.get('auth_mode')!='oauth2':raise RuntimeError('mf_oauth_not_enabled')
        now=now or datetime.now(timezone.utc)
        if now.tzinfo is None:raise ValueError('mf_oauth_timezone_required')
        current=config.get('access_token');expiration=config.get('expires_at_utc')
        try:expiry=datetime.fromisoformat(expiration.replace('Z','+00:00'))
        except (AttributeError,ValueError):expiry=None
        if not force_refresh and isinstance(current,str) and current and expiry and expiry.tzinfo and expiry>now+timedelta(seconds=120):return current
        application_id=config.get('application_id')
        if not isinstance(application_id,str) or not application_id or any(c.isspace() for c in application_id):raise RuntimeError('mf_oauth_credentials_missing')
        requester=requester or requests.post
        try:response=requester(ENDPOINT,headers={'Authorization':'Basic '+application_id},data={'grant_type':'client_credentials'},timeout=20,allow_redirects=False)
        except Exception:raise RuntimeError('mf_oauth_network_error') from None
        if response.status_code!=200:
            code=response.status_code
            if type(code) is not int:code=0
            raise RuntimeError('mf_oauth_http_'+str(code))
        try:data=response.json()
        except Exception:raise RuntimeError('mf_oauth_response_invalid') from None
        if not isinstance(data,dict):raise RuntimeError('mf_oauth_response_invalid')
        token=data.get('access_token');duration=data.get('expires_in')
        if not isinstance(token,str) or not token or any(c.isspace() for c in token) or type(duration) is not int or not 120<duration<=31_536_000 or str(data.get('token_type','')).lower()!='bearer':raise RuntimeError('mf_oauth_response_invalid')
        config.update(access_token=token,issued_at_utc=now.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),expires_at_utc=(now+timedelta(seconds=duration)).astimezone(timezone.utc).isoformat().replace('+00:00','Z'))
        try:save(path,config)
        except OSError:raise RuntimeError('mf_oauth_save_failed') from None
        return token


def authorized_get(profile,url,params=None,requester=None):
    """Une seule reprise après HTTP 401, exclusivement pour le fournisseur attendu."""
    from urllib.parse import urlparse
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.netloc!='public-api.meteofrance.fr' or not parsed.path.startswith('/public/') or parsed.query or parsed.fragment:
        raise ValueError('mf_resource_invalid')
    requester=requester or requests.get
    token=access_token(profile)
    for attempt in range(2):
        try:response=requester(url,headers={'Authorization':'Bearer '+token},params=params,timeout=25,allow_redirects=False)
        except Exception:raise RuntimeError('mf_resource_network_error') from None
        if response.status_code!=401 or attempt==1:return response
        token=access_token(profile,force_refresh=True)
    raise RuntimeError('mf_resource_unavailable')

"""Hourly Netatmo collector, activated only with independent private credentials."""
try:
    from installation_paths import installation_root
except ModuleNotFoundError:
    from raspberry.installation_paths import installation_root
import json
import math
import os
import tempfile
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from weather_protocol import IDENTITY_KEYS, UNITS, checksum, validate_row
from weather_outbox import enqueue

API='https://api.netatmo.com'
FIELDS={
 'temperature':('temperature','instant',None), 'humidity':('relative_humidity','instant',None),
 'pressure':('air_pressure','instant',None), 'rain_60min':('rainfall','rolling',3600),
 'rain_24h':('rainfall','unknown',None), 'rain_live':('rainfall','unknown',None),
 'wind_strength':('wind_speed','instant',None),'gust_strength':('wind_gust','instant',None),
 'wind_angle':('wind_direction','instant',None),'gust_angle':('gust_direction','instant',None),
 'Temperature':('temperature','instant',None),'Humidity':('relative_humidity','instant',None),
 'Pressure':('air_pressure','instant',None),'Rain':('rainfall','unknown',None),
 'sum_rain_1':('rainfall','unknown',None),'sum_rain_24':('rainfall','unknown',None),
 'WindStrength':('wind_speed','instant',None),'GustStrength':('wind_gust','instant',None),
 'WindAngle':('wind_direction','instant',None),'GustAngle':('gust_direction','instant',None)}

class Failure(Exception):
    def __init__(self,code,retry_after=0):self.code=code;self.retry_after=retry_after

def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,tmp=tempfile.mkstemp(dir=path.parent,suffix='.part')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,allow_nan=False);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:Path(tmp).unlink(missing_ok=True)

def utc(timestamp):
    if timestamp is None:return None
    try:
        number=Decimal(str(timestamp))
        if not number.is_finite() or number!=number.to_integral_value():raise ValueError()
        return datetime.fromtimestamp(int(number),timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    except (ValueError,TypeError,OverflowError,OSError):raise Failure('invalid_source_time') from None

def decimal_value(value):
    if value is None:return None
    if isinstance(value,bool) or not isinstance(value,(int,float,Decimal)):raise Failure('invalid_source_value')
    number=Decimal(str(value))
    if not number.is_finite():raise Failure('invalid_source_value')
    result=format(number,'f')
    if '.' in result:result=result.rstrip('0').rstrip('.')
    return '0' if number==0 else result

def row(source,station,module,field,value,stamp,retrieved):
    metric,kind,duration=FIELDS[field]
    date=utc(stamp)
    obs=dict(source=source,station_id=station,module_id=module,api_field=field,metric=metric,
      value=decimal_value(value),unit=UNITS[metric],source_time=date,time_precision='second' if date else 'unknown',
      period=dict(kind=kind,duration_seconds=duration,start=None,end=None),
      temporal_quality='source_timestamp' if date else 'missing_timestamp',
      provenance='netatmo:getpublicdata' if source=='netatmo_public' else 'netatmo:getstationsdata',supersedes=None)
    identity='w1_'+checksum({k:obs[k] for k in IDENTITY_KEYS}) if module is not None and date else 'wu1_'+str(uuid4())
    result=dict(observation_id=identity,revision_hash=checksum(obs),observation=obs,retrieved_at=retrieved)
    validate_row(result)
    return result

def public_rows(payload,targets,retrieved):
    if not isinstance(payload.get('body'),list):raise Failure('invalid_public_response')
    rows=[];found=set()
    for station in payload['body']:
        sid=station.get('_id')
        if sid not in targets:continue
        found.add(sid)
        for mid,measure in station.get('measures',{}).items():
            if not isinstance(measure,dict):continue
            for field in FIELDS:
                if field not in measure:continue
                stamp=measure.get('rain_timeutc') if field.startswith('rain') else measure.get('wind_timeutc')
                rows.append(row('netatmo_public',sid,mid or None,field,measure[field],stamp,retrieved))
            types=measure.get('type',[]);series=measure.get('res',{})
            if isinstance(types,list) and isinstance(series,dict):
                for stamp,values in series.items():
                    if not isinstance(values,list):continue
                    for index,field in enumerate(types):
                        if field in FIELDS and index<len(values):rows.append(row('netatmo_public',sid,mid or None,field,values[index],stamp,retrieved))
    return rows,sorted(set(targets)-found)

def personal_rows(payload,retrieved):
    body=payload.get('body',{})
    if not isinstance(body,dict) or not isinstance(body.get('devices'),list):raise Failure('invalid_personal_response')
    rows=[]
    for station in body['devices']:
        sid=station.get('_id')
        # Main-module pressure is useful outdoors; indoor temperature/humidity excluded.
        modules=[(station,{'Pressure'})]
        for mod in station.get('modules',[]):
            if mod.get('type') in ('NAModule1','NAModule2','NAModule3'):modules.append((mod,set(FIELDS)))
        for module,allowed in modules:
            data=module.get('dashboard_data') or {}
            for field in allowed:
                if field in FIELDS and field in data:rows.append(row('netatmo_personal',sid,module.get('_id'),field,data[field],data.get('time_utc'),retrieved))
    return rows

def http(url,token=None,form=None):
    from urllib.parse import urlencode
    headers={'Accept':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    data=urlencode(form).encode() if form else None
    try:
        with urlopen(Request(url,data=data,headers=headers),timeout=20) as response:
            raw=response.read(4_000_001)
            if len(raw)>4_000_000:raise Failure('response_too_large')
            result=json.loads(raw,parse_float=Decimal)
            if not isinstance(result,dict):raise Failure('invalid_response')
            if result.get('error'):raise Failure('api_error')
            return result
    except HTTPError as error:
        if error.code==429:
            header=error.headers.get('Retry-After','3600')
            try:retry=max(60,int(header))
            except (ValueError,TypeError):
                try:
                    from email.utils import parsedate_to_datetime
                    retry=max(60,math.ceil(parsedate_to_datetime(header).timestamp()-time.time()))
                except (ValueError,TypeError,AttributeError,OverflowError):retry=3600
            raise Failure('rate_limited',retry) from None
        if error.code==403:
            try:
                detail=json.loads(error.read(4096)).get('error',{})
                if str(detail.get('message','')).lower()=='access token expired':raise Failure('http_401')
            except (ValueError,AttributeError):pass
        raise Failure('http_'+str(error.code)) from None
    except (URLError,TimeoutError,OSError):raise Failure('network_unavailable') from None
    except (ValueError,TypeError):raise Failure('invalid_response') from None

class Client:
    def __init__(self,path,request=http):
        self.path=Path(path);self.config=json.loads(self.path.read_text());self.request=request;self.refreshed=False;self.calls=0
        if self.config.get('independent_authorization') is not True:raise Failure('independent_authorization_required')
    def refresh(self):
        if self.refreshed:raise Failure('authorization_required')
        self.refreshed=True;self.calls+=1
        try:r=self.request(API+'/oauth2/token',form={k:self.config[k] for k in ('client_id','client_secret','refresh_token')}|{'grant_type':'refresh_token'})
        except Failure as error:
            if error.code=='http_400':raise Failure('authorization_required') from None
            raise
        if not r.get('access_token') or not r.get('refresh_token'):raise Failure('invalid_oauth_response')
        lifetime=r.get('expires_in')
        if type(lifetime) is not int or lifetime<=0:raise Failure('invalid_oauth_response')
        self.config.update(access_token=r['access_token'],refresh_token=r['refresh_token'],expires_at=int(time.time())+lifetime)
        if 'scope' in r:self.config['scope']=r['scope']
        atomic(self.path,self.config)
    def get(self,endpoint,params=None):
        from urllib.parse import urlencode
        if not self.config.get('access_token') or self.config.get('expires_at',0)<=time.time()+60:self.refresh()
        url=API+'/api/'+endpoint+('?' + urlencode(params) if params else '')
        for attempt in range(2):
            self.calls+=1
            try:return self.request(url,token=self.config['access_token'])
            except Failure as error:
                if error.code=='http_401' and attempt==0:self.refresh();continue
                raise

def cycle(base,request=http):
    base=Path(base);status_path=base/'data/weather-status.json'
    try:old=json.loads(status_path.read_text())
    except (OSError,ValueError):old={}
    if old.get('retry_at',0)>time.time():return {'status':'backoff'}
    status={'checked_at':utc(int(time.time())),'sources':{},'last_success':old.get('last_success')}
    try:
        settings=json.loads((base/'config/weather.json').read_text())
        if settings.get('enabled') is not True:raise Failure('disabled')
        device=json.loads((base/'config/collector.json').read_text())['device_id']
        client=Client(base/'config/weather-oauth.json',request)
        targets=settings['public_station_ids'];bounds=settings['public_bounds']
        if not isinstance(targets,list) or not targets or set(bounds)!= {'lat_ne','lat_sw','lon_ne','lon_sw'}:raise Failure('invalid_settings')
        if not all(isinstance(s,str) and 0<len(s)<=256 for s in targets):raise Failure('invalid_settings')
        if not all(type(v) in (int,float) and math.isfinite(v) for v in bounds.values()):raise Failure('invalid_settings')
        if not (-90<=bounds['lat_sw']<bounds['lat_ne']<=90 and -180<=bounds['lon_sw']<bounds['lon_ne']<=180):raise Failure('invalid_settings')
        for source in ('personal','public'):
            try:
                payload=client.get('getstationsdata' if source=='personal' else 'getpublicdata',None if source=='personal' else {**bounds,'filter':'false'})
                retrieved=utc(int(time.time()))
                if source=='personal':rows=personal_rows(payload,retrieved);missing=[]
                else:rows,missing=public_rows(payload,targets,retrieved)
                added=enqueue(base/'data/weather.sqlite3',device,rows)
                status['sources'][source]={'status':'partial' if missing or not rows else 'ok','rows':len(rows),'added':added,'missing_station_count':len(missing),'retrieved_at':retrieved}
            except Failure as error:
                status['sources'][source]={'status':'error','code':error.code}
                if error.retry_after:status['retry_at']=int(time.time())+error.retry_after;break
        status['requests']=client.calls
        status['status']='ok' if len(status['sources'])==2 and all(s['status']=='ok' for s in status['sources'].values()) else 'partial'
        if status['status']=='ok':status['last_success']=status['checked_at']
    except Failure as error:
        status.update(status='error',code=error.code)
        if error.retry_after:status['retry_at']=int(time.time())+error.retry_after
    except Exception:status.update(status='error',code='configuration_or_storage_error')
    atomic(status_path,status)
    return status

if __name__=='__main__':
    import fcntl
    os.umask(0o077)
    base=installation_root()
    with (base/'data/weather-collector.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit(0)
        result=cycle(base)
        print(json.dumps(result))
        raise SystemExit(0 if result['status'] in ('ok','backoff') else 1)

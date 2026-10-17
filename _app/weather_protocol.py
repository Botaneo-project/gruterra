"""Contrat météo partagé PC/Pi, sans réseau, configuration ou dépendance externe."""
import hashlib
import json
import re
from datetime import datetime
from decimal import Decimal
from uuid import UUID

PROTOCOL = 'gruterra-weather-sync'
MAX_BYTES = 1_000_000
MAX_ROWS = 500
IDENTITY_KEYS = ('source','station_id','module_id','api_field','metric','source_time','time_precision','period')
OBS_KEYS = set(IDENTITY_KEYS) | {'value','unit','temporal_quality','provenance','supersedes'}
UNITS = {'rainfall':'mm','temperature':'degC','relative_humidity':'percent','air_pressure':'hPa','wind_speed':'km/h','wind_gust':'km/h','wind_direction':'degree','gust_direction':'degree'}

def require(condition):
    if not condition:
        raise ValueError('invalid_weather_contract')

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def checksum(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def exact(value, keys):
    require(isinstance(value,dict) and set(value)==set(keys))

def string(value):
    require(isinstance(value,str) and 0<len(value)<=256)

def instant(value):
    require(isinstance(value,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',value))
    try:return datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ')
    except ValueError:raise ValueError('invalid_weather_contract') from None

def identifier(value):
    string(value)
    if value.startswith('w1_'):
        require(re.fullmatch(r'w1_[0-9a-f]{64}',value))
    else:
        require(value.startswith('wu1_'))
        try:uid=UUID(value[4:])
        except ValueError:raise ValueError('invalid_weather_contract') from None
        require(uid.version==4 and str(uid)==value[4:])

def reference(value):
    exact(value,('observation_id','revision_hash'))
    identifier(value['observation_id'])
    require(isinstance(value['revision_hash'],str) and re.fullmatch(r'[0-9a-f]{64}',value['revision_hash']))

def validate_observation(obs):
    exact(obs,OBS_KEYS)
    require(obs['source'] in ('netatmo_public','netatmo_personal'))
    for field in ('station_id','api_field'):string(obs[field])
    if obs['module_id'] is not None:string(obs['module_id'])
    require(isinstance(obs['metric'],str) and obs['metric'] in UNITS)
    require(obs['unit']==UNITS[obs['metric']])
    value=obs['value']
    if value is not None:
        require(isinstance(value,str) and len(value)<=64 and re.fullmatch(r'-?(?:0|[1-9]\d*)(?:\.\d*[1-9])?',value) and value!='-0')
        number=Decimal(value)
        if obs['metric']!='temperature':require(number>=0)
        if obs['metric']=='relative_humidity':require(number<=100)
        if obs['metric'] in ('wind_direction','gust_direction'):require(number<=360)
    require(obs['time_precision'] in ('second','minute','unknown'))
    if obs['source_time'] is None:
        require(obs['time_precision']=='unknown' and obs['temporal_quality']=='missing_timestamp')
    else:
        time=instant(obs['source_time'])
        require(obs['time_precision']!='unknown' and obs['temporal_quality']=='source_timestamp')
        if obs['time_precision']=='minute':require(time.second==0)
    require(obs['provenance']==('netatmo:getpublicdata' if obs['source']=='netatmo_public' else 'netatmo:getstationsdata'))
    period=obs['period'];exact(period,('kind','duration_seconds','start','end'))
    require(period['kind'] in ('rolling','calendar_day','instant','unknown'))
    duration=period['duration_seconds']
    require(duration is None or type(duration) is int and duration>0)
    if period['kind']=='rolling':require(duration is not None)
    if period['kind'] in ('instant','unknown'):require(duration is None and period['start'] is None and period['end'] is None)
    require((period['start'] is None)==(period['end'] is None))
    if period['start'] is not None:
        start,end=instant(period['start']),instant(period['end']);require(start<end)
        if duration is not None:require((end-start).total_seconds()==duration)
    if obs['api_field']=='rain_60min':require(obs['metric']=='rainfall' and period['kind']=='rolling' and duration==3600)
    require(obs['supersedes'] is None or isinstance(obs['supersedes'],dict))
    if obs['supersedes'] is not None:reference(obs['supersedes'])

def validate_row(row):
    exact(row,('observation_id','revision_hash','observation','retrieved_at'))
    reference({'observation_id':row['observation_id'],'revision_hash':row['revision_hash']})
    obs=row['observation'];validate_observation(obs);instant(row['retrieved_at'])
    # Module inconnu : wu1_ prioritaire, même si la date est connue.
    if obs['module_id'] is None or obs['source_time'] is None:
        require(row['observation_id'].startswith('wu1_'))
    else:
        require(row['observation_id']=='w1_'+checksum({key:obs[key] for key in IDENTITY_KEYS}))
    require(row['revision_hash']==checksum(obs))
    if obs['supersedes'] is not None:require(obs['supersedes']['observation_id']!=row['observation_id'])

def _pairs(rows):
    pairs=[(row['observation_id'],row['revision_hash']) for row in rows]
    require(len(pairs)==len(set(pairs)))

def validate_batch(batch, device_id):
    exact(batch,('protocol','protocol_version','observation_schema_version','device_id','rows','pending'))
    require(batch['protocol']==PROTOCOL and type(batch['protocol_version']) is int and batch['protocol_version']==1)
    require(type(batch['observation_schema_version']) is int and batch['observation_schema_version']==1)
    string(batch['device_id']);require(batch['device_id']==device_id)
    require(isinstance(batch['rows'],list) and len(batch['rows'])<=MAX_ROWS)
    require(type(batch['pending']) is int and batch['pending']>=len(batch['rows']))
    require(batch['pending']==0 or bool(batch['rows']))
    for row in batch['rows']:validate_row(row)
    _pairs(batch['rows']);require(len(canonical(batch))<=MAX_BYTES)
    return batch

def validate_ack(ack,device_id):
    exact(ack,('protocol','protocol_version','device_id','rows'))
    require(ack['protocol']==PROTOCOL and type(ack['protocol_version']) is int and ack['protocol_version']==1 and ack['device_id']==device_id)
    require(isinstance(ack['rows'],list) and len(ack['rows'])<=MAX_ROWS)
    for row in ack['rows']:reference(row)
    _pairs(ack['rows']);require(len(canonical(ack))<=MAX_BYTES)
    return ack

def decode(raw):
    require(isinstance(raw,bytes) and len(raw)<=MAX_BYTES and not raw.startswith(b'\xef\xbb\xbf'))
    def unique(pairs):
        result={}
        for key,value in pairs:
            require(key not in result);result[key]=value
        return result
    def invalid(value):raise ValueError('invalid_weather_contract')
    try:return json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=invalid)
    except (UnicodeError,ValueError,RecursionError):raise ValueError('invalid_weather_contract') from None

def pack_batch(rows,pending,device_id,max_bytes=MAX_BYTES):
    require(type(max_bytes) is int and 0<max_bytes<=MAX_BYTES)
    batch={'protocol':PROTOCOL,'protocol_version':1,'observation_schema_version':1,'device_id':device_id,'rows':[],'pending':pending}
    for row in rows:
        validate_row(row)
        candidate={**batch,'rows':batch['rows']+[row]}
        if len(canonical(candidate))>max_bytes or len(candidate['rows'])>MAX_ROWS:break
        batch=candidate
    if pending and not batch['rows']:raise ValueError('weather_row_exceeds_batch_limit')
    require(len(canonical(batch))<=max_bytes)
    return validate_batch(batch,device_id)

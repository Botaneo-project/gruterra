"""Shared PC/Pi lighting-window analysis; no interpolation or exposure claims."""
import json
import math
import os
import re
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

def date_eclairage(value):
    """Naive local readings stay local; aware readings use the schedule's Paris zone."""
    at = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    return at.astimezone(ZoneInfo('Europe/Paris')).replace(tzinfo=None) if at.tzinfo else at


def validate(start, end):
    for value in (start, end):
        if not isinstance(value, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value):
            raise ValueError('Utiliser HH:MM, par exemple 09:50.')
    if start == end:
        raise ValueError('Les heures doivent être différentes.')
    return {'start': start, 'end': end}

def profile(item):
    result=validate(item['start'],item['end'])
    if 'history' in item:
        history=[]
        for row in item['history']:
            day=datetime.strptime(row['from'],'%Y-%m-%d').date().isoformat()
            history.append(dict(validate(row['start'],row['end']), **{'from':day}))
        if not history or len(history)>2000 or [r['from'] for r in history]!=sorted(set(r['from'] for r in history)):
            raise ValueError('Invalid schedule history')
        if validate(history[-1]['start'],history[-1]['end'])!=result:raise ValueError('History mismatch')
        result['history']=history
    return result

def load(path, key):
    try:
        item = json.loads(Path(path).read_text(encoding='utf-8')).get(str(key))
        return profile(item) if item else None
    except (OSError, ValueError, TypeError, KeyError):
        return None

@contextmanager
def locked(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.with_suffix('.lock').open('a+b') as stream:
        stream.seek(0)
        if os.name=='nt':
            import msvcrt
            if stream.read(1)==b'':stream.write(b'0');stream.flush()
            stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX)
        try:yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)

def save(path, key, start, end, _locked=False, _profile=None, _day=None):
    if not _locked:
        with locked(path):return save(path,key,start,end,_locked=True,_profile=_profile,_day=_day)
    item = validate(start, end)
    path = Path(path)
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    previous=data.get(str(key))
    if _profile is not None:
        item=profile(_profile)
    elif previous:
        old=profile(previous)
        if validate(old['start'],old['end'])==item:
            item=old
        else:
            day=_day or datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()
            datetime.strptime(day,'%Y-%m-%d')
            history=old.get('history',[dict(validate(old['start'],old['end']), **{'from':'0001-01-01'})])
            if history[-1]['from']>day:raise ValueError('Clock precedes saved history')
            item['history']=[r for r in history if r['from']<day]+[dict(item,**{'from':day})]
    data[str(key)] = item
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    os.chmod(temp, 0o600)
    os.replace(temp, path)
    return item

def analyse_profile(points, item):
    item=profile(item)
    history=item.get('history',[dict(validate(item['start'],item['end']),**{'from':'0001-01-01'})])
    result=[]
    for i,row in enumerate(history):
        until=history[i+1]['from'] if i+1<len(history) else '9999-12-31'
        for group in analyse(points,row['start'],row['end']):
            if row['from']<=group['day']<until:
                result.append(dict(group,start=row['start'],end=row['end']))
    return sorted(result,key=lambda g:g['day'],reverse=True)

def analyse(points, start, end):
    validate(start, end)
    groups = {}
    for point in points:
        try:
            at = date_eclairage(point['at'])
            value = float(point['lux'])
            if not math.isfinite(value) or value < 0:
                continue
            hour = at.strftime('%H:%M')
            inside = start <= hour < end if start < end else hour >= start or hour < end
            if not inside:
                continue
            day = at.date() - timedelta(days=1) if start > end and hour < end else at.date()
            groups.setdefault(day.isoformat(), []).append(dict(point, lux=value))
        except (ValueError, TypeError, KeyError):
            continue
    return [dict(day=day,count=len(rows),mean=sum(p['lux'] for p in rows)/len(rows),minimum=min(p['lux'] for p in rows),maximum=max(p['lux'] for p in rows),points=sorted(rows,key=lambda p:date_eclairage(p['at']))) for day,rows in sorted(groups.items(),reverse=True)]

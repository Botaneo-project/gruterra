"""Préparation AROME-PI : métadonnées et calendrier, sans réseau ni jeton."""
import re,math
import xml.etree.ElementTree as ET
from datetime import datetime,timedelta,timezone

FIELD=re.compile(r'^TOTAL_WATER_PRECIPITATION__GROUND_OR_WATER_SURFACE___(\d{4}-\d{2}-\d{2}T\d{2}\.\d{2}\.\d{2}Z)_PT15M$')

def aware(value):
    if not isinstance(value,datetime) or value.tzinfo is None:raise ValueError('arome_timezone_required')
    return value.astimezone(timezone.utc)

def next_scan(now):
    now=aware(now)
    candidate=now.replace(minute=(now.minute//15)*15,second=1,microsecond=0)
    if candidate<=now:candidate+=timedelta(minutes=15)
    return candidate

def xml(raw):
    if not isinstance(raw,bytes) or len(raw)>5_000_000 or b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:raise ValueError('arome_invalid_metadata')
    try:return ET.fromstring(raw)
    except ET.ParseError:raise ValueError('arome_invalid_metadata') from None

def run_time(identifier):
    match=FIELD.fullmatch(identifier or '')
    if not match:raise ValueError('arome_invalid_field')
    return datetime.strptime(match[1],'%Y-%m-%dT%H.%M.%SZ').replace(tzinfo=timezone.utc)

def latest_rain(raw,now):
    now=aware(now);candidates=[]
    for node in xml(raw).iter():
        if node.tag.split('}')[-1]!='CoverageId':continue
        try:run=run_time(node.text)
        except ValueError:continue
        if run<=now:candidates.append((run,node.text))
    if not candidates:raise ValueError('arome_no_recent_field')
    run,identifier=max(candidates)
    # Les anciens calculs du catalogue ne deviennent pas une prévision actuelle.
    if now>=run+timedelta(hours=6):raise ValueError('arome_no_future_steps')
    return identifier

def description(raw,identifier,now):
    now=aware(now);run=run_time(identifier);root=xml(raw)
    coverage=next((node for node in root.iter() if node.tag.split('}')[-1]=='CoverageDescription' and any(value==identifier for value in node.attrib.values())),None)
    if coverage is None:raise ValueError('arome_wrong_coverage')
    unit=next((node.attrib.get('code') for node in coverage.iter() if node.tag.split('}')[-1]=='uom'),None)
    if unit!='kg m-2':raise ValueError('arome_unknown_rain_unit')
    axis=next((node for node in coverage.iter() if node.tag.split('}')[-1]=='GeneralGridAxis' and any(child.tag.split('}')[-1]=='gridAxesSpanned' and (child.text or '').strip()=='time' for child in node)),None)
    if axis is None:raise ValueError('arome_missing_time_axis')
    coefficients=next((node.text for node in axis if node.tag.split('}')[-1]=='coefficients'),'')
    try:steps=[int(value) for value in (coefficients or '').split()]
    except ValueError:raise ValueError('arome_invalid_time_axis') from None
    if not steps or steps!=sorted(set(steps)) or any(step<900 or step>21600 or step%900 for step in steps):raise ValueError('arome_invalid_time_axis')
    lower=next((node.text for node in coverage.iter() if node.tag.split('}')[-1]=='lowerCorner'),None)
    upper=next((node.text for node in coverage.iter() if node.tag.split('}')[-1]=='upperCorner'),None)
    try:bounds=[float(v) for text in (lower,upper) for v in text.split()]
    except (ValueError,AttributeError):raise ValueError('arome_invalid_bounds') from None
    if len(bounds)!=4 or not all(math.isfinite(v) for v in bounds):raise ValueError('arome_invalid_bounds')
    if not (-180<=bounds[0]<bounds[2]<=180 and -90<=bounds[1]<bounds[3]<=90):raise ValueError('arome_invalid_bounds')
    future=[]
    for step in steps:
        end=run+timedelta(seconds=step)
        if end<=now:continue
        future.append({'lead_seconds':step,'valid_at':end.isoformat().replace('+00:00','Z')})
    if not future:raise ValueError('arome_no_future_steps')
    return {'kind':'forecast','model':'AROME-PI','coverage_id':identifier,'run_at':run.isoformat().replace('+00:00','Z'),'source_unit':unit,'bounds':bounds,'steps':future,'period_seconds':900,'accumulation_semantics_verified':False}

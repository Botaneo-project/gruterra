"""Read-only, explainable post-watering context for one physical sensor.

No inferred irrigation, interpolated values or learned optimal thresholds.
The existing session grouping and cycle quality services remain authoritative.
"""
import json
import math
import re
from datetime import timedelta
from botaneo_dates import vers_local_naif
from i18n import traduire_courant as t
from services.analyse_arrosage import analyser_qualite_cycle


def _number(value, maximum=None):
    if isinstance(value, bool): return None
    try: value=float(value)
    except (ValueError, TypeError, OverflowError): return None
    return value if math.isfinite(value) and value>=0 and (maximum is None or value<=maximum) else None


def _eligible(row):
    """Explicit test/exclusion metadata is respected; raw values are never changed."""
    raw=row[6] if len(row)>6 else None
    if not raw: return True
    if isinstance(raw,str):
        try: raw=json.loads(raw)
        except (ValueError,TypeError): return True  # Historical free text has no quality contract.
    if not isinstance(raw,dict): return True
    return not (raw.get('is_test') is True or raw.get('manual_test') is True
                or raw.get('exclude_from_analysis') is True
                or raw.get('quality') in ('test','invalid','suspect','excluded'))


def observer_session(session, rows, sensor_id, now, *, next_start=None, threshold=20):
    """Observe a session with a bounded baseline and independent metric validity.

    Timestamps use the existing Paris date conversion. Conflicting values at one
    timestamp are excluded per metric, rather than averaged. Bursts are not used
    as independent temporal evidence: trend checks require four hourly buckets.
    """
    start=vers_local_naif(session.get('date_debut'));end=vers_local_naif(session.get('date_fin'))
    now=vers_local_naif(now)
    if start is None or end is None or now is None or end<start or end>now:return None
    stop=min(now,vers_local_naif(next_start)-timedelta(microseconds=1)) if next_start else now
    by_time={};excluded=0
    for row in rows:
        if len(row)<8 or row[7]!=sensor_id:continue
        at=vers_local_naif(row[1])
        if at is None or at>stop or at<start-timedelta(hours=24):continue
        if not _eligible(row):excluded+=1;continue
        values=by_time.setdefault(at,{'soil':set(),'ec':set()})
        for key,index,maximum in (('soil',3,100),('ec',5,None)):
            value=_number(row[index],maximum)
            if value is not None:values[key].add(value)
    conflicts=sum(len(v)>1 for values in by_time.values() for v in values.values())
    metrics={key:sorted((at,next(iter(values[key]))) for at,values in by_time.items() if len(values[key])==1) for key in ('soil','ec')}
    result={'start':start,'end':end,'days':(now-start).total_seconds()/86400,
            'volume':_number(session.get('quantite_totale_ml')),'fractions':len(session.get('apports') or []),
            'threshold':threshold,'excluded':excluded,'conflicts':conflicts,'sensor_id':sensor_id}
    for key,points in metrics.items():
        before=[p for p in points if p[0]<start];after=[p for p in points if p[0]>end]
        # Readings during a split session do not represent the final response.
        result[key+'_before']=before[-1] if before else None
        result[key+'_after']=after[0] if after else None
        result[key+'_latest']=after[-1] if after else None
        result[key+'_points']=after
    soil=result['soil_points'];baseline=result['soil_before'];first=result['soil_after']
    result['peak']=max(soil,key=lambda p:p[1]) if soil else None
    result['peak_delay_h']=(result['peak'][0]-end).total_seconds()/3600 if soil else None
    result['amplitude']=result['peak'][1]-baseline[1] if soil and baseline else None
    peak=result['peak'];post_peak=[p for p in soil if peak and p[0]>=peak[0]]
    quality=analyser_qualite_cycle(soil)
    result['max_gap_h']=quality['plus_grand_trou_h']
    buckets={at.replace(minute=0,second=0,microsecond=0) for at,value in post_peak}
    span=(post_peak[-1][0]-post_peak[0][0]).total_seconds()/3600 if post_peak else 0
    reliable=(len(buckets)>=4 and span>=6 and result['max_gap_h']<=8 and not conflicts)
    result['drying_rate_day']=(post_peak[-1][1]-post_peak[0][1])/span*24 if reliable else None
    # Return is an observed crossing bracket, not an exact interpolated moment.
    result['return_bracket']=None
    if baseline and peak and peak[1]>baseline[1]:
        for left,right in zip(post_peak,post_peak[1:]):
            if left[1]>baseline[1]>=right[1] and (right[0]-left[0]).total_seconds()<=8*3600:
                result['return_bracket']=(left[0],right[0]);break
    result['confidence']='limited' if (not baseline or not first or conflicts or excluded or len({p[0].replace(minute=0,second=0,microsecond=0) for p in soil})<4 or result['max_gap_h']>8) else 'descriptive'
    fresh=bool(soil and 0<=(now-soil[-1][0]).total_seconds()<48*3600)
    changed=bool(baseline and peak and peak[1]>baseline[1])
    ec_changed=bool(result['ec_before'] and result['ec_after'] and result['ec_after'][1]>result['ec_before'][1])
    result['state']='waiting' if not fresh else ('response' if changed else ('ec_only' if ec_changed else 'no_response'))
    if reliable and result['drying_rate_day']<=-3:result['state']='falling'
    result['level']='attention' if result['state'] in ('waiting','no_response','ec_only','falling') or (fresh and soil[-1][1]<threshold) else 'info'
    return result


def message(observation, sensor):
    def value(point):return f'{point[1]:g}' if point else '—'
    r=observation
    lines=[t('watering_context_event').format(volume=f"{r['volume']:g} ml" if r['volume'] is not None else '—',date=r['start'].strftime('%d/%m/%Y %H:%M'),count=r['fractions'],days=f"{r['days']:.1f}",sensor=sensor),
           t('watering_context_soil').format(before=value(r['soil_before']),after=value(r['soil_after']),latest=value(r['soil_latest']))]
    if r['ec_before'] or r['ec_after']:
        lines.append(t('watering_context_ec').format(before=value(r['ec_before']),after=value(r['ec_after'])))
    lines.append(t('watering_context_'+r['state']))
    if r['soil_latest'] and r['soil_latest'][1]<r['threshold']:
        lines.append(t('watering_context_threshold').format(threshold=r['threshold']))
    lines.append(t('watering_context_confidence_'+r['confidence']))
    if r['excluded'] or r['conflicts']:lines.append(t('watering_context_excluded').format(count=r['excluded'],conflicts=r['conflicts']))
    lines.append(t('watering_context_limits'))
    return ' '.join(lines)


def charger_contextes(db, plant_id, sensors, now):
    """Reuse current database queries. No schema change or write operation."""
    if not callable(getattr(db,'get_derniere_session_arrosage',None)):return {}
    session=db.get_derniere_session_arrosage(plant_id)
    if not session:return {}
    end=vers_local_naif(session.get('date_fin'))
    if end is None or not 0<=(now-end).total_seconds()<=48*3600:return {}
    result={}
    for sensor in sensors:
        rows=db.get_mesures_capteur(sensor[0],limite=-1)
        observation=observer_session(session,rows,sensor[0],now)
        if observation:result[sensor[0]]={'niveau':observation['level'],'detail':message(observation,sensor[1]),'observation':observation}
    return result


def observer_cycles(sessions, rows, sensor_id, now):
    """Prepare descriptive historical markers without learning a target value.

    Each cycle stops before the next session, even when a later session occurred
    today. No cross-sensor pooling or statistical health claim is made.
    """
    ordered=sorted((s for s in sessions if vers_local_naif(s.get('date_debut')) is not None),
                   key=lambda s:vers_local_naif(s['date_debut']))
    result=[]
    for index,session in enumerate(ordered):
        following=ordered[index+1]['date_debut'] if index+1<len(ordered) else None
        observation=observer_session(session,rows,sensor_id,now,next_start=following)
        if observation:result.append(observation)
    return result


def dernier_signal_sante(db,plant_id,now):
    if not callable(getattr(db,'get_journal_plante',None)):return None
    records=[(vers_local_naif(row[2]),row) for row in db.get_journal_plante(plant_id,limite=-1) if row[3]=='evaluation_sante']
    records=sorted(((at,row) for at,row in records if at is not None and at<=now),key=lambda item:item[0],reverse=True)
    for at,row in records:
        detail=row[5] or ''
        # Structured state only; no diagnosis from arbitrary user prose.
        signs=re.search(r'\bsignes=([a-z_,]+)',detail)
        concerning=bool(signs and set(signs.group(1).split(',')) & {'leaf_drop','soft_leaf','brown_spot','soft_stem'})
        if 'etat_sante=degrade' in detail or 'etat_sante=a_surveiller' in detail or concerning:
            return t('watering_context_health').format(date=at.strftime('%d/%m/%Y %H:%M'))
        return None
    return None

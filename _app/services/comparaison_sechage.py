"""Descriptive comparison on the same post-watering window, no interpolation."""
from datetime import timedelta
import math
from botaneo_dates import vers_local_naif
from i18n import traduire_courant as t


def observer(cycle):
    watering=cycle.get('arrosage') or {}
    anchor=vers_local_naif(watering.get('date_fin') if isinstance(watering,dict) else watering[2])
    result={'state':'insufficient','date':cycle.get('date'),'rate':None,'count':0,'gap_h':None,'source':None,'reason':'no_readings'}
    if anchor is None:
        result['reason']='no_anchor';return result
    start=anchor+timedelta(hours=24);end=anchor+timedelta(hours=72)
    points=[];all_dates=[]
    for row in cycle.get('mesures',[]):
        at=vers_local_naif(row[1])
        if at is None:continue
        all_dates.append(at)
        try:value=float(row[3]) if row[3] is not None and not isinstance(row[3],bool) else None
        except (TypeError,ValueError):continue
        if value is not None and math.isfinite(value) and 0<=value<=100 and at>=anchor:
            points.append((at,value,row[7] if len(row)>7 else None))
    points.sort(key=lambda point:point[0])
    if not points:
        if cycle.get('fin') is None:result['state']='waiting'
        return result
    latest=max(all_dates)
    if latest<end-timedelta(hours=2):
        result['state']='waiting' if cycle.get('fin') is None else 'insufficient'
        return result
    first=min(points,key=lambda p:abs((p[0]-start).total_seconds()))
    last=min(points,key=lambda p:abs((p[0]-end).total_seconds()))
    if abs((first[0]-start).total_seconds())>7200 or abs((last[0]-end).total_seconds())>7200:
        result['reason']='endpoint_missing';return result
    selected=[p for p in points if first[0]<=p[0]<=last[0]]
    sources={p[2] for p in selected}
    result['count']=len(selected)
    if len(sources)!=1 or None in sources:
        result['state']='source_uncertain';return result
    # Contradictory values at one timestamp are not averaged or selected arbitrarily.
    by_time={}
    for at,value,_ in selected:by_time.setdefault(at,set()).add(value)
    if any(len(values)>1 for values in by_time.values()):
        result['reason']='contradiction';return result
    unique=sorted((at,next(iter(values))) for at,values in by_time.items())
    gap=max(((b[0]-a[0]).total_seconds()/3600 for a,b in zip(unique,unique[1:])),default=0)
    result['gap_h']=gap
    if len(unique)<4:
        result['reason']='few_points';return result
    if gap>8:
        result['reason']='gap';return result
    if last[0]<=first[0]:
        result['reason']='no_duration';return result
    hours=(last[0]-first[0]).total_seconds()/3600
    result.update(state='ready',source=next(iter(sources)),rate=(last[1]-first[1])/hours*24,
                  start=first[0],end=last[0],hours=hours,start_value=first[1],end_value=last[1])
    return result


def resume(cycles):
    observations=[observer(cycle) for cycle in cycles]
    lines=[t('drying_compare_window')]
    for observation in observations:
        date=observation['date']
        label=date.strftime('%d/%m/%Y') if date else '—'
        if observation['state']=='ready':
            lines.append(t('drying_compare_observed').format(date=label,start=observation['start'].strftime('%d/%m %H:%M'),end=observation['end'].strftime('%d/%m %H:%M'),first=f"{observation['start_value']:g}",last=f"{observation['end_value']:g}",rate=f"{observation['rate']:+.2f}",count=observation['count'],gap=f"{observation['gap_h']:.1f}"))
        elif observation['state']=='insufficient':
            reason=t('drying_compare_reason_'+observation['reason']).format(gap=f"{observation['gap_h'] or 0:.1f}")
            lines.append(t('drying_compare_insufficient_detail').format(date=label,reason=reason))
        else:
            lines.append(t('drying_compare_'+observation['state']).format(date=label))
    if observations:
        recent=observations[-1]
        previous=next((r for r in reversed(observations[:-1]) if r['state']=='ready' and recent['state']=='ready' and r['source']==recent['source']),None)
        if previous:
            # Both values remain visible; no universal threshold for plant health.
            lines.append(t('drying_compare_reference').format(date=previous['date'].strftime('%d/%m/%Y'),delta=f"{recent['rate']-previous['rate']:+.2f}"))
        else:lines.append(t('drying_compare_no_reference'))
    lines.append(t('drying_compare_water_context'))
    lines.append(t('drying_compare_limits'))
    return '\n'.join(lines)

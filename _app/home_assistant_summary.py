"""Home/health summary of the separate HA archive. No network or token decryption."""
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import os
from home_assistant_sensors import utc
from sensor_source_policy import hardware_id


def summarize(mappings, rows, *, plant_names=None, now=None):
    instant=datetime.fromisoformat(utc(now)) if now else datetime.now(timezone.utc)
    groups={}
    for mapping in mappings:
        physical=hardware_id(mapping.get('hardware_id'))
        group=groups.setdefault(physical,{'hardware_id':physical,'model':mapping['model'],'plant_id':mapping.get('plant_id'),'test_data':False,'metrics':[]})
        group['test_data'] |= mapping.get('test_data') is True
        if any(r['metric']==mapping['metric'] for r in group['metrics']):continue
        candidates=sorted([r for r in rows if r['hardware_id']==physical and r['metric']==mapping['metric']],key=lambda r:r['ha_updated_at'],reverse=True)
        # Prefer a genuine archived state over a reconstructed window-start state.
        row=next((r for r in candidates if r.get('timing_kind')!='initial_state_uncertain'),candidates[0] if candidates else None)
        item={'metric':mapping['metric'],'value':None,'unit':None,'at':None,'status':'missing','age_minutes':None}
        if row:
            stamp=row.get('ha_value_changed_at') if row.get('timing_kind')=='ha_attribute_update' else row['ha_updated_at']
            item.update(value=row['value'],unit=row['unit'],at=stamp,retrieved_at=row.get('gruterra_retrieved_at'))
            age=(instant-datetime.fromisoformat(utc(stamp))).total_seconds() if stamp else None
            item['age_minutes']=max(0,int(age/60)) if age is not None else None
            if row['status']!='available':item['status']=row['status']
            elif row.get('timing_kind')=='initial_state_uncertain':item['status']='uncertain'
            elif age is None:item['status']='uncertain'
            elif age < -300:item['status']='future'
            else:item['status']='stale' if age>7200 else 'recent'
            if item['status'] in ('recent','stale'):
                from home_assistant_chart import chart_data,group_bursts
                model=chart_data(candidates,mapping['metric'])
                if model:
                    latest=group_bursts(model['points'])[-1]
                    values={point[1] for point in latest}
                    if len(values)>1 and latest[-1][0]==datetime.fromisoformat(utc(row['ha_updated_at'])).timestamp():
                        item['value']=f'{min(values):g}–{max(values):g}'
                        item['status']='burst_conflict'

        group['metrics'].append(item)
    for group in groups.values():
        group['plant_name']=(plant_names or {}).get(group['plant_id'])
    return list(groups.values())


def load_summary():
    if os.environ.get('BOTANEO_DEMO')=='1':
        from home_assistant_demo import preview
        from home_assistant_timing import timing
        records=preview()['records']
        mappings=[{k:r[k] for k in ('hardware_id','model','metric','test_data')} for r in records]
        return {'ok':True,'demo':True,'devices':summarize(mappings,[{**r,**timing(r)} for r in records])}
    from botaneo_config import CONFIG_DIR,DATA_DIR,lire_json
    from home_assistant_view import read_rows,plants
    path=CONFIG_DIR/'home_assistant.local.json'
    if not path.is_file():return {'ok':True,'devices':[]}
    try:
        mappings=lire_json(path)['entities']
        try:names=dict(plants())
        except Exception:names={}
        archive=Path(DATA_DIR)/'home_assistant_history.sqlite3'
        # Separate limits prevent a busy light sensor hiding slower soil/air quantities.
        rows=[]
        for mapping in mappings:
            rows.extend(read_rows(archive,[mapping],limit=50))
        return {'ok':True,'devices':summarize(mappings,rows,plant_names=names)}
    except Exception:return {'ok':False,'devices':[]}


def device_label(device):
    from i18n import traduire_courant as t
    name=device.get('plant_name') or t('ha_view_unassigned')
    return name+(' · '+t('ha_home_test') if device['test_data'] else '')+' · '+device['model']+' · …'+device['hardware_id'][-4:]


def metric_line(row):
    from i18n import traduire_courant as t
    value=(row['value']+' '+(row['unit'] or '')) if row['value'] is not None else '—'
    stamp=datetime.fromisoformat(row['at']).astimezone(ZoneInfo('Europe/Paris')).strftime('%d/%m %H:%M') if row['at'] else '—'
    return t('ha_home_line').format(metric=t('ha_metric_'+row['metric']),value=value,date=stamp,status=t('ha_home_status_'+row['status']),age=t('ha_home_age').format(minutes=row['age_minutes']) if row['age_minutes'] is not None else t('ha_home_age_unknown'))


def health_lines(summary=None):
    from i18n import traduire_courant as t
    summary=summary if summary is not None else load_summary()
    if not summary['ok']:return ['',t('ha_home_title'),t('ha_home_failed')]
    if not summary['devices']:return []
    lines=['',t('ha_home_title'),t('ha_home_note')]
    for device in summary['devices']:
        lines.append(device_label(device))
        lines.extend('  '+metric_line(row) for row in device['metrics'])
    return lines


def card(parent,palette):
    import tkinter as tk
    from i18n import traduire_courant as t
    palette={'GREEN':palette['BLUE'],'SECONDARY':palette['TEXT'],**palette}
    frame=tk.Frame(parent,bg=palette['CARD'],highlightbackground=palette['BORDER'],highlightthickness=1)
    frame.pack(fill='x',padx=20,pady=(0,12))
    timer=None
    def refresh():
        nonlocal timer
        if timer:
            frame.after_cancel(timer);timer=None
        for child in frame.winfo_children():child.destroy()
        summary=load_summary()
        tk.Label(frame,text=t('ha_home_title'),font=('Segoe UI',12,'bold'),bg=palette['CARD'],fg=palette['GREEN'],anchor='w').pack(fill='x',padx=12,pady=(10,4))
        labels=[]
        def label(text,color):
            widget=tk.Label(frame,text=text,bg=palette['CARD'],fg=color,justify='left',anchor='w',wraplength=700)
            widget.pack(fill='x',padx=12,pady=3);labels.append(widget)
        label(t('ha_home_note'),palette['SECONDARY'])
        if not summary['ok']:label(t('ha_home_failed'),palette['TEXT'])
        elif not summary['devices']:label(t('ha_home_empty'),palette['SECONDARY'])
        for device in summary['devices']:
            label(device_label(device),palette['BLUE'])
            for row in device['metrics']:label(metric_line(row),palette['TEXT'])
        from home_assistant_dashboard import open_window
        tk.Button(frame,text=t('ha_view_title'),command=lambda:open_window(parent.winfo_toplevel(),palette),bg=palette['LIGHT_BLUE'],fg=palette['BLUE']).pack(anchor='w',padx=12,pady=(4,10))
        frame.bind('<Configure>',lambda e:[w.configure(wraplength=max(140,e.width-26)) for w in labels])
        timer=frame.after(60000,refresh)
    event_root=frame._root()
    bindings={event:event_root.bind(event,lambda event:refresh(),add='+') for event in ('<<GruterraAssociationsChanged>>','<<GruterraDataChanged>>')}
    def destroyed(event):
        if event.widget is frame:
            if timer:
                try:frame.after_cancel(timer)
                except tk.TclError:pass
            for name,binding in bindings.items():
                try:event_root.unbind(name,binding)
                except tk.TclError:pass
    frame.bind('<Destroy>',destroyed)
    refresh()
    return frame

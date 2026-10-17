"""Three-way lighting settings sync. Conflicts never overwrite either side."""
import json
from i18n import traduire_courant as t
import os
from pathlib import Path
from light_schedule import load, save, locked, validate, profile

from botaneo_config import CONFIG_DIR
ROOT=CONFIG_DIR

def decision(base, pc, pi, known):
    if pc == pi:return 'equal'
    if not known:
        if pc is None:return 'pull'
        if pi is None:return 'push'
        return 'conflict'
    if pc == base:return 'pull'
    if pi == base:return 'push'
    return 'conflict'

def synchronize(config, sender=None, resolve=None):
    if os.environ.get('BOTANEO_DEMO')=='1' or config.get('away') or not config.get('enabled'):
        return t('lamp_sync_disabled')
    from raspberry_sync import transport
    import database
    sender=sender or transport
    schedules=ROOT/'light-schedules.json';statefile=ROOT/'light-sync-state.json'
    db=database.get_connection()
    try:rows=db.execute('SELECT plante_id,UPPER(adresse_ble) FROM capteurs WHERE actif=1 AND plante_id IS NOT NULL').fetchall()
    finally:db.close()
    allowed={s.upper() for s in config.get('sensors',[])}
    rows=[(str(p),s) for p,s in rows if s in allowed]
    # Ambiguous associations require manual correction, never a guessed mapping.
    rows=[(p,s) for p,s in rows if sum(a==p for a,b in rows)==1 and sum(b==s for a,b in rows)==1]
    if not rows:return t('lamp_sync_unmapped')
    conflicts=0;changed=0
    with locked(schedules):
        state=json.loads(statefile.read_text()) if statefile.exists() else {}
        for plant,sensor in rows:
            key=config['device_id']+'|'+sensor
            entry=state.get(key,{})
            pc=load(schedules,plant)
            response=sender(config,'lamp_get',{'sensor':sensor})
            if response.get('device_id')!=config['device_id']:raise ValueError(t('lamp_sync_identity'))
            pi=response['value']
            if pi is not None:pi=profile(pi)
            action=decision(entry.get('base'),pc,pi,'base' in entry)
            if resolve and resolve.get('plant')==plant and action=='conflict':
                # A deliberate choice applies to the freshly read values shown by UI.
                if resolve['pc']!=pc or resolve['pi']!=pi:raise ValueError(t('lamp_sync_changed'))
                action='push' if resolve['choice']=='pc' else 'pull'
            if action=='push':
                if pc and pc.get('history') and response.get('schedule_version',1)<2:raise ValueError(t('lamp_sync_failed'))
                answer=sender(config,'lamp_set',{'sensor':sensor,'expected':pi,'value':pc})
                if answer.get('device_id')!=config['device_id'] or not answer.get('ok'):
                    state[key]={'base':entry.get('base'),'conflict':True,'plant':plant,'pc':pc,'pi':pi};conflicts+=1;continue
                pi=pc;changed+=1
            elif action=='pull':
                if pi is None:
                    conflicts+=1;state[key]={**entry,'conflict':True,'plant':plant,'pc':pc,'pi':pi};continue
                save(schedules,plant,pi['start'],pi['end'],_locked=True,_profile=pi);pc=pi;changed+=1
            elif action=='conflict':
                conflicts+=1;state[key]={**entry,'conflict':True,'plant':plant,'pc':pc,'pi':pi};continue
            state[key]={'base':pc,'plant':plant,'conflict':False}
        tmp=statefile.with_suffix('.tmp');tmp.write_text(json.dumps(state));os.replace(tmp,statefile)
    return t('lamp_sync_summary').format(count=changed)+(t('lamp_sync_conflicts').format(count=conflicts) if conflicts else t('lamp_sync_equal'))

def format_times(value):
    if not value:return t('lamp_sync_missing')
    text=value['start']+'–'+value['end']
    for row in value.get('history',[]):
        text+='\n'+row['from']+' : '+row['start']+'–'+row['end']
    return text

def resolve_window(parent,plant):
    from tkinter import messagebox
    if os.environ.get('BOTANEO_DEMO')=='1':
        messagebox.showinfo(t('lighting_error_title'),t('lighting_demo_sync_disabled'),parent=parent)
        return
    from suivi_raspberry import load_config
    from raspberry_sync import config_path
    try:
        config=load_config(config_path())
        message=synchronize(config)
        statefile=ROOT/'light-sync-state.json'
        state=json.loads(statefile.read_text()) if statefile.exists() else {}
        entries=[e for k,e in state.items() if k.startswith(config['device_id']+'|') and e.get('plant')==str(plant) and e.get('conflict')]
        for entry in entries:
            pc,pi=entry['pc'],entry['pi']
            choice=messagebox.askyesnocancel(t('lamp_sync_conflict_title'),t('lamp_sync_choice').format(pc=format_times(pc),pi=format_times(pi)),parent=parent)
            if choice is None:return
            message=synchronize(config,resolve={'plant':str(plant),'pc':pc,'pi':pi,'choice':'pc' if choice else 'pi'})
        messagebox.showinfo(t('lamp_sync_title'),message,parent=parent)
    except Exception:
        messagebox.showerror(t('lamp_sync_title'),t('lamp_sync_failed'),parent=parent)

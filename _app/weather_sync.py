from raspberry_paths import remote_command, remote_backup
from botaneo_config import DATA_DIR
"""Raccordement SSH météo dédié, sans collecte Netatmo ni gestion OAuth."""
import subprocess
import threading
from pathlib import Path
from weather_protocol import canonical,decode,validate_batch,validate_ack,PROTOCOL
from weather_store import import_batch

LOCK=threading.Lock()

def transport(config,operation,request=None):
    from suivi_raspberry import validate
    validate(config)
    if operation not in ('weather_export','weather_ack'):raise ValueError('weather_unknown_operation')
    if operation=='weather_ack':validate_ack(request,config['device_id'])
    elif request is not None:raise ValueError('weather_unexpected_request')
    args=['ssh','-i',config['key'],'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2',config['user']+'@'+config['host'],remote_command(config, 'sync_export.py', operation)]
    try:
        result=subprocess.run(args,input=canonical(request) if request is not None else None,capture_output=True,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except (OSError,subprocess.TimeoutExpired):raise ConnectionError('weather_transport_unavailable') from None
    if result.returncode:raise ConnectionError('weather_remote_operation_failed')
    return decode(result.stdout)

def synchronize(config=None,sender=None,db_path=None,max_batches=20):
    if config is None:
        from suivi_raspberry import load_config
        from raspberry_sync import config_path
        try:config=load_config(config_path())
        except (OSError,ValueError):return {'ok':False,'status':'disabled','added':0,'duplicates':0,'revisions':0,'pending':None}
    totals={'added':0,'duplicates':0,'revisions':0}
    if config.get('away') or not config.get('enabled') or config.get('weather_import_enabled') is not True:
        return {'ok':False,'status':'disabled',**totals,'pending':None}
    if type(max_batches) is not int or not 1<=max_batches<=20:raise ValueError('weather_invalid_batch_limit')
    real_transport=sender is None and db_path is None
    def finished(result):
        if real_transport and result.get('ok'):
            try:
                from weather_backup_pc import retrieve
                result['backup_status']=retrieve(config)
            except Exception:
                result['backup_status']='failed'
        return result
    sender=sender or transport
    path=Path(db_path) if db_path is not None else DATA_DIR/'netatmo_pluie.sqlite3'
    stage='export';pending=None
    with LOCK:
        try:
            for _ in range(max_batches):
                stage='export';batch=sender(config,'weather_export')
                stage='validation';validate_batch(batch,config['device_id'])
                pending=batch['pending']
                if not batch['rows']:return finished({'ok':True,'status':'empty' if not sum(totals.values()) else 'complete',**totals,'pending':0})
                stage='import';counts,ack=import_batch(path,batch,config['device_id'])
                for key in totals:totals[key]+=counts[key]
                stage='ack';response=sender(config,'weather_ack',ack)
                if not isinstance(response,dict) or set(response)!= {'protocol','protocol_version','device_id','confirmed'}:raise ValueError('weather_invalid_ack_response')
                if response['protocol']!=PROTOCOL or type(response['protocol_version']) is not int or response['protocol_version']!=1 or response['device_id']!=config['device_id'] or type(response['confirmed']) is not int or response['confirmed']!=len(ack['rows']):raise ValueError('weather_invalid_ack_response')
                pending-=len(batch['rows'])
                if pending==0:return finished({'ok':True,'status':'complete',**totals,'pending':0})
            return {'ok':True,'status':'partial',**totals,'pending':pending}
        except Exception:
            # Jamais l'exception brute, stderr SSH, un identifiant ou une configuration.
            return {'ok':False,'status':'failed','stage':stage,**totals,'pending':pending}


def result_message(result):
    from i18n import traduire_courant as t
    status=result.get('status')
    if status=='disabled':return ''
    if status=='failed':return t('weather_pi_sync_failed').format(stage=result.get('stage','export'))
    suffix=(' · '+t('weather_pi_backup_'+result['backup_status'])) if result.get('backup_status') else ''
    if status=='empty':return t('weather_pi_sync_empty')+suffix
    return t('weather_pi_sync_done').format(added=result.get('added',0),duplicates=result.get('duplicates',0),revisions=result.get('revisions',0),pending=result.get('pending',0))+suffix

def preferences(parent,palette):
    import os
    import tkinter as tk
    from tkinter import messagebox
    from i18n import traduire_courant as t
    from suivi_raspberry import load_config,save_config
    from raspberry_sync import config_path
    from meteo_nappes import harmoniser
    if os.environ.get('BOTANEO_DEMO')=='1':
        messagebox.showinfo(t('weather_pi_preferences'),t('weather_pi_demo'),parent=parent);return
    try:config=load_config(config_path())
    except (OSError,ValueError):
        messagebox.showinfo(t('weather_pi_preferences'),t('weather_pi_config_missing'),parent=parent);return
    window=tk.Toplevel(parent);window.title(t('weather_pi_preferences'))
    enabled=tk.BooleanVar(value=config.get('weather_import_enabled') is True)
    tk.Checkbutton(window,text=t('weather_pi_import_enable'),variable=enabled).pack(anchor='w',padx=18,pady=12)
    from netatmo_pi_credentials_ui import open_window
    tk.Button(window,text=t('netatmo_pi_credentials_title'),command=lambda:open_window(window,palette)).pack(anchor='w',padx=18,pady=8)
    tk.Label(window,text=t('weather_pi_import_explanation'),wraplength=540,justify='left').pack(fill='x',padx=18,pady=12)
    def save():
        try:
            current=load_config(config_path());current['weather_import_enabled']=enabled.get();save_config(config_path(),current)
        except (OSError,ValueError):messagebox.showerror(t('weather_pi_preferences'),t('weather_pi_save_failed'),parent=window);return
        window.destroy()
    tk.Button(window,text=t('groundwater_save'),command=save).pack(anchor='e',padx=18,pady=12)
    import weather_view
    tk.Button(window,text=t('weather_pi_observations'),command=lambda:weather_view.open_window(window,palette=palette)).pack(anchor='w',padx=18,pady=10)
    harmoniser(window,palette)

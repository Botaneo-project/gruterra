"""Réglage privé AROME-PI ; aucune requête lors de l'ouverture ou de la sauvegarde."""
from botaneo_config import CONFIG_DIR,lire_json,ecrire_json
PATH=CONFIG_DIR/'meteofrance_arome_pi.local.json'

def load(path=PATH):
    if not path.exists():return {'schema_version':1,'enabled':False,'auth_mode':'bearer','application_id':'','access_token':'','issued_at_utc':None,'expires_at_utc':None}
    return lire_json(path)

def save_credentials(mode,application_id,token,path=PATH):
    if mode not in ('bearer','oauth2'):raise ValueError('mf_auth_mode_invalid')
    values=[]
    for value in (application_id,token):
        if not isinstance(value,str):raise ValueError('mf_auth_value_invalid')
        value=value.strip()
        if len(value)>8192 or any(c.isspace() for c in value):raise ValueError('mf_auth_value_invalid')
        values.append(value)
    application_id,token=values
    if mode=='oauth2' and not application_id or mode=='bearer' and not token:raise ValueError('mf_auth_credentials_missing')
    config=load(path)
    changed=config.get('auth_mode')!=mode or config.get('application_id','')!=application_id or config.get('access_token','')!=token
    config.update(auth_mode=mode,application_id=application_id,access_token=token)
    if changed:config.update(issued_at_utc=None,expires_at_utc=None)
    path.parent.mkdir(parents=True,exist_ok=True);ecrire_json(path,config)

def open_window(parent,palette):
    import tkinter as tk
    from i18n import traduire_courant as t
    from meteo_nappes import harmoniser
    window=tk.Toplevel(parent);window.title(t('arome_auth_title'));window.geometry('670x470');window.minsize(560,440)
    try:config=load()
    except RuntimeError:config={}
    tk.Label(window,text=t('arome_auth_note'),wraplength=610,justify='left').pack(fill='x',padx=18,pady=12)
    mode=tk.StringVar(value=config.get('auth_mode') if config.get('auth_mode') in ('bearer','oauth2') else 'bearer')
    tk.Radiobutton(window,text=t('arome_auth_oauth'),variable=mode,value='oauth2').pack(anchor='w',padx=18)
    tk.Radiobutton(window,text=t('arome_auth_manual'),variable=mode,value='bearer').pack(anchor='w',padx=18)
    fields={};entries=[]
    for field,key in (('application_id','arome_auth_application'),('access_token','arome_auth_token')):
        tk.Label(window,text=t(key),anchor='w').pack(fill='x',padx=18,pady=(10,0))
        fields[field]=tk.StringVar(value=config.get(field,'') if isinstance(config.get(field,''),str) else '')
        entry=tk.Entry(window,textvariable=fields[field],show='•');entry.pack(fill='x',padx=18,pady=(3,8));entries.append(entry)
    reveal=tk.BooleanVar(value=False)
    def show():
        for entry in entries:entry.configure(show='' if reveal.get() else '•')
    tk.Checkbutton(window,text=t('netatmo_pi_reveal'),variable=reveal,command=show).pack(anchor='w',padx=18)
    status=tk.StringVar();tk.Label(window,textvariable=status,wraplength=610,justify='left').pack(fill='x',padx=18,pady=10)
    def save():
        try:save_credentials(mode.get(),fields['application_id'].get(),fields['access_token'].get())
        except (OSError,ValueError,RuntimeError):status.set(t('arome_auth_invalid'));return
        status.set(t('arome_auth_saved'))
    tk.Button(window,text=t('netatmo_pi_save_credentials'),command=save).pack(anchor='e',padx=18,pady=10)
    harmoniser(window,palette)

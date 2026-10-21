"""Saisie locale d'un accès Pi distinct ; aucun transfert ou renouvellement automatique."""
from botaneo_config import CONFIG_DIR,lire_json,ecrire_json

PATH=CONFIG_DIR/'netatmo_raspberry_oauth.local.json'
FIELDS=('client_id','client_secret','access_token','refresh_token')

def load(path=PATH):
    if not path.exists():return dict(schema_version=1,independent_authorization=False,client_id='',client_secret='',access_token='',refresh_token='',expires_at=0)
    return lire_json(path)

def save_fields(values,path=PATH):
    before=load(path)
    updated=dict(before)
    for field in FIELDS:
        value=values.get(field,'')
        if not isinstance(value,str):raise ValueError('netatmo_pi_invalid_field')
        value=value.strip()
        if len(value)>8192 or any(character.isspace() for character in value):raise ValueError('netatmo_pi_invalid_field')
        updated[field]=value
    changed=any(updated[field]!=before.get(field,'') for field in FIELDS)
    if changed:updated.update(independent_authorization=False,expires_at=0)
    updated.setdefault('schema_version',1)
    path.parent.mkdir(parents=True,exist_ok=True)
    ecrire_json(path,updated)
    return changed

def open_window(parent,palette):
    import tkinter as tk
    from i18n import traduire_courant as t
    from meteo_nappes import harmoniser
    window=tk.Toplevel(parent);window.title(t('netatmo_pi_credentials_title'));window.geometry('610x520');window.minsize(500,360)
    from ui_scroll_form import create
    body,footer=create(window,palette)
    tk.Button(footer,text=t('close'),command=window.destroy).pack(side='right',padx=(8,0))
    tk.Label(body,text=t('netatmo_pi_credentials_note'),wraplength=560,justify='left').pack(fill='x',padx=18,pady=14)
    try:config=load()
    except RuntimeError:config={}
    entries={};values={}
    for field in FIELDS:
        tk.Label(body,text=t('netatmo_pi_field_'+field),anchor='w').pack(fill='x',padx=18)
        values[field]=tk.StringVar(value=config.get(field,'') if isinstance(config.get(field,''),str) else '')
        entry=tk.Entry(body,textvariable=values[field],show='' if field=='client_id' else '•')
        entry.pack(fill='x',padx=18,pady=(2,10));entries[field]=entry
    reveal=tk.BooleanVar(value=False)
    def show():
        for field,entry in entries.items():
            if field!='client_id':entry.configure(show='' if reveal.get() else '•')
    tk.Checkbutton(body,text=t('netatmo_pi_reveal'),variable=reveal,command=show).pack(anchor='w',padx=18)
    status=tk.StringVar();tk.Label(body,textvariable=status,wraplength=560,justify='left').pack(fill='x',padx=18,pady=10)
    def save():
        try:save_fields({field:value.get() for field,value in values.items()})
        except (OSError,ValueError,RuntimeError):status.set(t('netatmo_pi_save_error'));return
        status.set(t('netatmo_pi_saved_local'))
    tk.Button(footer,text=t('netatmo_pi_save_credentials'),command=save).pack(side='right')
    harmoniser(window,palette)
    return window

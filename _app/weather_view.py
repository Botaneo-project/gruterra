"""Read-only view of imported weather, preserving source dates and revisions."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from weather_store import analysis_candidates

def observations(path):
    path=Path(path)
    if not path.exists():return []
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='weather_observations_v1'").fetchone():return []
        rows=db.execute('SELECT observation_id,revision_hash,observation_json,retrieved_at FROM weather_observations_v1 ORDER BY retrieved_at DESC LIMIT 300').fetchall()
    accepted={(r['observation_id'],r['revision_hash']) for r in analysis_candidates(path)}
    result=[]
    for identity,digest,content,retrieved in rows:
        o=json.loads(content);p=o['period']
        result.append(dict(station=o['station_id'],module=o['module_id'],source=o['source'],field=o['api_field'],value=o['value'],unit=o['unit'],measured=o['source_time'],retrieved=retrieved,period=p,selected=(identity,digest) in accepted))
    return result

def open_window(parent,path=None,palette=None):
    import tkinter as tk
    from tkinter import ttk
    from i18n import traduire_courant as t
    from ui_palette import THEME_CLAIR,THEME_SOMBRE
    from meteo_nappes import harmoniser
    if palette is None:
        try:dark=parent.cget('background').lower()==THEME_SOMBRE['BG'].lower()
        except (tk.TclError,AttributeError):dark=False
        palette=THEME_SOMBRE if dark else THEME_CLAIR
    path=path or Path(__file__).resolve().parent/'data/netatmo_pluie.sqlite3'
    window=tk.Toplevel(parent);window.title(t('weather_pi_observations'));window.geometry('1120x560');window.minsize(620,360)
    footer=tk.Frame(window);footer.pack(side='bottom',fill='x',padx=16,pady=8)
    tk.Button(footer,text=t('close'),command=window.destroy).pack(side='right',padx=(8,0))
    tk.Label(window,text=t('weather_pi_observations_note'),wraplength=1000,justify='left').pack(fill='x',padx=16,pady=12)
    frame=tk.Frame(window);frame.pack(fill='both',expand=True,padx=16,pady=8)
    columns=('station','module','source','field','value','unit','measured','retrieved','period','state')
    table=ttk.Treeview(frame,columns=columns,show='headings')
    for name in columns:
        table.heading(name,text=t('weather_pi_col_'+name));table.column(name,width=160 if name in ('station','module','measured','retrieved') else 120,stretch=False)
    vertical=ttk.Scrollbar(frame,orient='vertical',command=table.yview)
    horizontal=ttk.Scrollbar(frame,orient='horizontal',command=table.xview)
    table.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set)
    table.grid(row=0,column=0,sticky='nsew');vertical.grid(row=0,column=1,sticky='ns');horizontal.grid(row=1,column=0,sticky='ew')
    frame.rowconfigure(0,weight=1);frame.columnconfigure(0,weight=1)
    status=tk.StringVar();tk.Label(footer,textvariable=status,wraplength=300,justify='left').pack(side='left',fill='x',expand=True)
    def refresh():
        try:rows=observations(path)
        except (ValueError,sqlite3.Error,OSError):status.set(t('weather_pi_view_error'));return
        table.delete(*table.get_children())
        for r in rows:
            p=r['period'];period=t('weather_pi_period_'+p['kind'])+((' · '+str(p['duration_seconds'])+' s') if p['duration_seconds'] else '')
            table.insert('', 'end',values=(r['station'],r['module'] or '—',t('weather_pi_source_'+r['source']),r['field'],r['value'] if r['value'] is not None else t('weather_pi_missing'),r['unit'],r['measured'] or '—',r['retrieved'],period,t('weather_pi_selected' if r['selected'] else 'weather_pi_excluded')))
        status.set(t('weather_pi_view_count').format(count=len(rows)))
    tk.Button(footer,text=t('weather_pi_view_refresh'),command=refresh).pack(side='right')
    def resize(event):
        if event.widget is window:
            for child in window.winfo_children():
                if isinstance(child,tk.Label):child.configure(wraplength=max(240,event.width-32))
    window.bind('<Configure>',resize,add='+')
    harmoniser(window,palette)
    refresh()
    return window

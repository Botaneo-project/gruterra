"""Read-only view of imported weather, preserving source dates and revisions."""
from botaneo_config import DATA_DIR
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
        result.append(dict(row_id=identity+':'+digest,station=o['station_id'],module=o['module_id'],source=o['source'],field=o['api_field'],value=o['value'],unit=o['unit'],measured=o['source_time'],retrieved=retrieved,period=p,selected=(identity,digest) in accepted))
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
    path=path or DATA_DIR/'netatmo_pluie.sqlite3'
    window=tk.Toplevel(parent);window.title(t('weather_pi_observations'));window.geometry('1120x560');window.minsize(620,360)
    footer=tk.Frame(window);footer.pack(side='bottom',fill='x',padx=16,pady=8)
    status=tk.StringVar()
    status_label=tk.Label(footer,textvariable=status,wraplength=580,justify='left',anchor='w')
    status_label.pack(fill='x',pady=(0,6))
    actions=tk.Frame(footer);actions.pack(fill='x')
    tk.Button(actions,text=t('close'),command=window.destroy).pack(side='right',padx=(8,0))
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
    def refresh(event=None):
        from botaneo_dates import maintenant_local, parse_iso
        try:
            rows=observations(path)
            rendered=[]
            for index,r in enumerate(rows):
                p=r['period']
                period=t('weather_pi_period_'+p['kind'])+((' · '+str(p['duration_seconds'])+' s') if p['duration_seconds'] else '')
                rendered.append((r.get('row_id',str(index)),(r['station'],r['module'] or '—',t('weather_pi_source_'+r['source']),
                    r['field'],r['value'] if r['value'] is not None else t('weather_pi_missing'),r['unit'],
                    r['measured'] or t('weather_source_date_unknown'),r['retrieved'] or t('weather_source_date_unknown'),
                    period,t('weather_pi_selected' if r['selected'] else 'weather_pi_excluded'))))
            # Prepare every display row before touching the existing view.
            if len({identity for identity,values in rendered})!=len(rendered):raise ValueError('duplicate display identity')
            dates=[r['retrieved'] for r in rows if parse_iso(r['retrieved']) is not None]
            when=maintenant_local().strftime('%d/%m/%Y %H:%M:%S')
            state=t('weather_pi_view_count').format(count=len(rows)) if rows else t('weather_pi_no_imported_data')
            state+=' · '+t('history_local_read').format(refreshed=when)
            if dates:
                # Retrieval is deliberately labelled separately from measurement time.
                from botaneo_dates import vers_utc
                latest=max(dates,key=vers_utc)
                state+=' · '+t('weather_pi_latest_retrieval').format(date=latest)
        except (ValueError,TypeError,KeyError,sqlite3.Error,OSError):
            status.set(t('weather_pi_view_stale') if table.get_children() else t('weather_pi_view_error'))
            return
        selected=table.selection();x,y=table.xview(),table.yview()
        table.delete(*table.get_children())
        for identity,values in rendered:table.insert('', 'end',iid=identity,values=values)
        for item in selected:
            if table.exists(item):table.selection_add(item)
        if x:table.xview_moveto(x[0])
        if y:table.yview_moveto(y[0])
        status.set(state)
    tk.Button(actions,text=t('weather_pi_view_refresh'),command=refresh).pack(side='left')
    def resize(event):
        if event.widget is window:
            status_label.configure(wraplength=max(240,event.width-40))
            for child in window.winfo_children():
                if isinstance(child,tk.Label):child.configure(wraplength=max(240,event.width-32))
    window.bind('<Configure>',resize,add='+')
    window.bind('<<GruterraDataChanged>>',refresh,add='+')
    harmoniser(window,palette)
    refresh()
    return window

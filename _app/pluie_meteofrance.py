"""Pluie Météo-France indépendante des plantes et de l'authentification Netatmo."""
import csv,io,json,math,sqlite3,hashlib,threading
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
from queue import Queue,Empty
import requests
from botaneo_config import CONFIG_DIR,lire_json,parametres_netatmo
from i18n import traduire_courant as t

BASE='https://public-api.meteofrance.fr/public/DPObs/v2'
DB=Path(__file__).resolve().parent/'data/meteofrance_pluie.sqlite3'

def utc(value):
    if not isinstance(value,str):raise ValueError('rain_invalid_date')
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None:raise ValueError('rain_invalid_date')
    return result.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')

def nearest(rows,latitude,longitude):
    def distance(lat,lon):
        a,b=map(math.radians,(latitude,lat));x=math.sin((b-a)/2)**2+math.cos(a)*math.cos(b)*math.sin(math.radians(lon-longitude)/2)**2
        return 6371000*2*math.asin(min(1,math.sqrt(x)))
    result=[]
    for row in rows:
        try:
            lat=float(row['Latitude'].replace(',','.'));lon=float(row['Longitude'].replace(',','.'))
            if not -90<=lat<=90 or not -180<=lon<=180:continue
            code=row['Id_station']
            if not isinstance(code,str) or not code.isdigit() or len(code)!=8:continue
            result.append({'station':code,'name':row['Nom_usuel'],'distance_m':round(distance(lat,lon))})
        except (ValueError,TypeError,KeyError):continue
    return sorted(result,key=lambda row:row['distance_m'])[:5]

def normalise(data,station):
    if isinstance(data,dict) and isinstance(data.get('features'),list):data=data['features']
    if not isinstance(data,list):raise ValueError('rain_invalid_response')
    rows=[]
    for item in data:
        if not isinstance(item,dict):continue
        item=item.get('properties',item)
        if not isinstance(item,dict) or 'rr1' not in item:continue
        value=item['rr1']
        if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or value<0):continue
        code=item.get('geo_id_insee')
        if code is not None and str(code)!=station['station']:continue
        try:measured=utc(item.get('validity_time'))
        except (ValueError,TypeError):continue
        rows.append({**station,'measured':measured,'mm':value,'field':'rr1','period_seconds':3600,'unit':'mm'})
    return rows

def save(path,rows):
    if not rows:return 0
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(path)) as db,db:
        db.execute('CREATE TABLE IF NOT EXISTS rainfall_v1 (digest TEXT PRIMARY KEY,station TEXT NOT NULL,name TEXT NOT NULL,distance_m INTEGER,measured TEXT NOT NULL,mm REAL,period_seconds INTEGER NOT NULL,retrieved TEXT NOT NULL)')
        before=db.total_changes
        retrieved=datetime.now(timezone.utc).isoformat(timespec='seconds')
        for row in rows:
            # Même date et nouvelle valeur : correction conservée, sans écrasement.
            digest=hashlib.sha256(json.dumps({k:row[k] for k in ('station','measured','mm','field','period_seconds','unit')},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            db.execute('INSERT OR IGNORE INTO rainfall_v1 VALUES (?,?,?,?,?,?,?,?)',(digest,row['station'],row['name'],row['distance_m'],row['measured'],row['mm'],row['period_seconds'],retrieved))
        return db.total_changes-before

def read(path=DB):
    path=Path(path)
    if not path.exists():return []
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        return db.execute('SELECT name,distance_m,measured,mm FROM rainfall_v1 ORDER BY measured DESC,distance_m LIMIT 200').fetchall()

def collect(point=None):
    config=lire_json(CONFIG_DIR/'meteofrance.local.json');key=config.get('api_key')
    if not isinstance(key,str) or not key.strip():raise ValueError('rain_key_missing')
    if point is None:latitude,longitude,*_=parametres_netatmo()
    else:latitude,longitude=point
    if any(type(value) not in (int,float) or not math.isfinite(value) for value in (latitude,longitude)) or not -90<=latitude<=90 or not -180<=longitude<=180:raise ValueError('rain_invalid_location')
    with requests.Session() as session:
        session.headers.update({'Authorization':'Bearer '+key.strip()})
        response=session.get(BASE+'/liste-stations',timeout=20,allow_redirects=False)
        if response.status_code!=200:return [],response.status_code
        if len(response.content)>10_000_000:raise ValueError('rain_response_too_large')
        stations=nearest(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig')),delimiter=';'),latitude,longitude)
        rows=[]
        for station in stations:
            response=session.get(BASE+'/station/horaire',params={'id_station':station['station'],'format':'json'},timeout=20,allow_redirects=False)
            if response.status_code in (401,403,429):return rows,response.status_code
            if response.status_code!=200:continue
            if len(response.content)>1_000_000:raise ValueError('rain_response_too_large')
            rows.extend(normalise(response.json(),station))
        return rows,200


def netatmo_snapshot(path=None, station_id=None):
    """Consultation du cache existant uniquement : aucune requête ni archive."""
    from meteo_synthese import choisir_mesure
    path=Path(path) if path is not None else Path(__file__).resolve().parent/'data/netatmo_cache.json'
    try:cache=lire_json(path)
    except RuntimeError:return []
    stations=cache.get('stations_publiques',[])
    if not isinstance(stations,list):return []
    # Une sélection explicite ou les favoris locaux, jamais une station du développeur.
    candidates=[station for station in stations if isinstance(station,dict) and
                (station.get('id')==station_id if station_id is not None else station.get('favorite') is True)]
    def distance_key(station):
        value=station.get('distance_m')
        return value if type(value) in (int,float) and math.isfinite(value) and value>=0 else math.inf
    selected=min(candidates,key=distance_key,default=None)
    if selected is None:return []
    result=[]
    for metric in ('pluie_1h','pluie_24h'):
        info=choisir_mesure(metric,[],[selected],lambda station:station.get('nom') or 'Netatmo',lambda value,unit:str(value))
        if info.get('etat')!='ok':continue
        distance=selected.get('distance_m')
        if type(distance) not in (int,float) or not math.isfinite(distance) or distance<0:distance=None
        result.append({'station':selected.get('nom') or 'Netatmo','distance_m':distance,'date':info.get('date'),'mm':info['valeur'],'period_hours':1 if metric=='pluie_1h' else 24})
    return result

def open_window(parent,palette):
    import os
    import tkinter as tk
    from tkinter import ttk
    from meteo_nappes import harmoniser
    window=tk.Toplevel(parent);window.title(t('mf_rain_title'));window.geometry('1000x740');window.minsize(620,440)
    footer=tk.Frame(window);footer.pack(side='bottom',fill='x',padx=16,pady=12)
    tk.Button(footer,text=t('close'),command=window.destroy).pack(side='right',padx=(8,0))
    tk.Label(window,text=t('mf_rain_note'),wraplength=780,justify='left').pack(fill='x',padx=16,pady=12)
    status=tk.StringVar(value=t('mf_rain_local'));tk.Label(window,textvariable=status,wraplength=780,justify='left').pack(fill='x',padx=16)
    postal=tk.StringVar()
    towns=[];active_rows=None
    line=tk.Frame(window);line.pack(fill='x',padx=16,pady=8)
    line.columnconfigure(1,weight=1)
    tk.Label(line,text=t('mf_rain_postcode')).grid(row=0,column=0,sticky='w')
    entry=tk.Entry(line,textvariable=postal,width=8);entry.grid(row=0,column=1,sticky='ew',padx=8)
    commune=ttk.Combobox(line,state='readonly',width=32);commune.grid(row=1,column=0,columnspan=3,sticky='ew',pady=(8,0))
    comparison=tk.StringVar()
    tk.Label(window,textvariable=comparison,wraplength=940,justify='left').pack(fill='x',padx=16,pady=8)
    tk.Label(window,text=t('mf_rain_compare_note'),wraplength=940,justify='left').pack(fill='x',padx=16,pady=(0,8))
    frame=tk.Frame(window);frame.pack(fill='both',expand=True,padx=16,pady=12)
    style=ttk.Style(window);style.configure('MFRain.Treeview',background=palette['CARD'],fieldbackground=palette['CARD'],foreground=palette['TEXT']);style.configure('MFRain.Treeview.Heading',background=palette['BG'],foreground=palette['TEXT'])
    table=ttk.Treeview(frame,columns=('station','distance','date','mm'),show='headings',style='MFRain.Treeview')
    for field,key in zip(('station','distance','date','mm'),('mf_rain_station','mf_rain_distance','mf_rain_date','mf_rain_mm')):table.heading(field,text=t(key));table.column(field,width=180,minwidth=100)
    scrollbar=ttk.Scrollbar(frame,command=table.yview);scrollbar.pack(side='right',fill='y');table.configure(yscrollcommand=scrollbar.set);table.pack(fill='both',expand=True)
    def display():
        snapshots=netatmo_snapshot() if not postal.get().strip() else []
        lines=[t('mf_rain_compare_title')]
        for snapshot in snapshots:
            distance='—' if snapshot['distance_m'] is None else f"{snapshot['distance_m']/1000:.2f} km"
            lines.append(t('mf_rain_compare_row').format(station=snapshot['station'],distance=distance,mm=f"{snapshot['mm']:g}",hours=snapshot['period_hours'],date=snapshot['date'] or '—'))
        if not snapshots:lines.append(t('mf_rain_postcode_comparison') if postal.get().strip() else t('mf_rain_compare_missing'))
        comparison.set('\n'.join(lines))
        table.delete(*table.get_children())
        shown=[(name,None,measured,mm) for name,distance,measured,mm in read()] if active_rows is None else [(r['name'],r['distance_m'],r['measured'],r['mm']) for r in active_rows]
        for name,distance,measured,mm in shown:
            local=datetime.fromisoformat(measured.replace('Z','+00:00')).astimezone().strftime('%d/%m/%Y %H:%M %z')
            table.insert('','end',values=(name,'—' if distance is None else f'{distance/1000:.2f} km',local,'—' if mm is None else f'{mm:g} mm'))
    queue=Queue();busy=False
    def poll():
        nonlocal busy,active_rows
        if not window.winfo_exists():return
        try:kind,rows,http,error=queue.get_nowait()
        except Empty:window.after(100,poll);return
        busy=False;button.configure(state='normal');town_button.configure(state='normal');entry.configure(state='normal');commune.configure(state='readonly')
        if error:status.set(t('mf_rain_town_error') if kind=='towns' else t('mf_rain_error'));return
        if kind=='towns':
            towns[:]=rows;commune['values']=[town['name']+' · '+town['code'] for town in towns]
            if len(towns)==1:commune.current(0)
            else:commune.set('')
            status.set(t('mf_rain_choose_town') if towns else t('mf_rain_no_town'));return
        active_rows=rows
        try:count=save(DB,rows);display()
        except (OSError,sqlite3.Error,ValueError):status.set(t('mf_rain_error'));return
        status.set(t('mf_rain_done').format(count=count) if http==200 else t('mf_rain_http').format(status=http))
    def refresh():
        nonlocal busy
        if busy:return
        if os.environ.get('BOTANEO_DEMO')=='1':status.set(t('mf_rain_demo'));return
        point=None
        if postal.get().strip():
            index=commune.current()
            if index<0:status.set(t('mf_rain_choose_town'));return
            point=(towns[index]['latitude'],towns[index]['longitude'])
        busy=True;button.configure(state='disabled');town_button.configure(state='disabled');entry.configure(state='disabled');commune.configure(state='disabled');status.set(t('mf_rain_loading'))
        def worker():
            try:rows,http=collect(point);queue.put(('rain',rows,http,False))
            except Exception:queue.put(('rain',[],None,True))
        threading.Thread(target=worker,daemon=True).start();window.after(100,poll)
    def invalidate(*args):
        nonlocal active_rows
        towns.clear();commune.set('');commune['values']=[];active_rows=[];display()
    postal.trace_add('write',invalidate)
    def town_changed(event=None):
        nonlocal active_rows
        active_rows=[];display()
    commune.bind('<<ComboboxSelected>>',town_changed)
    def find_towns():
        nonlocal busy,active_rows
        if busy:return
        from communes_meteo import postcode,search
        try:code=postcode(postal.get())
        except ValueError:status.set(t('mf_rain_postcode_invalid'));return
        if os.environ.get('BOTANEO_DEMO')=='1':status.set(t('mf_rain_demo'));return
        towns.clear();commune.set('');commune['values']=[];active_rows=[];display()
        busy=True;button.configure(state='disabled');town_button.configure(state='disabled');entry.configure(state='disabled');commune.configure(state='disabled')
        status.set(t('mf_rain_search_town'))
        def worker():
            try:queue.put(('towns',search(code),200,False))
            except Exception:queue.put(('towns',[],None,True))
        threading.Thread(target=worker,daemon=True).start();window.after(100,poll)
    town_button=tk.Button(line,text=t('mf_rain_find_town'),command=find_towns);town_button.grid(row=0,column=2,sticky='e')
    button=tk.Button(footer,text=t('mf_rain_refresh'),command=refresh);button.pack(side='right')
    def resize(event):
        if event.widget is window:
            for child in window.winfo_children():
                if isinstance(child,tk.Label):child.configure(wraplength=max(240,event.width-32))
    window.bind('<Configure>',resize,add='+')
    harmoniser(window,palette)
    try:display()
    except (sqlite3.Error,ValueError):status.set(t('mf_rain_error'))

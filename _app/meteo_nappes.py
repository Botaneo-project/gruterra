"""Hub'Eau : consultation facultative, à la demande, sans localisation automatique."""
import json
import math
import re
import threading
import ssl
import socket
from urllib.error import HTTPError, URLError
from queue import Queue, Empty
from urllib.parse import urlencode
from urllib.request import urlopen
from datetime import date, timedelta
from botaneo_config import CONFIG_DIR, lire_json, ecrire_json
from i18n import traduire_courant as t

CONFIG = CONFIG_DIR / 'nappes.local.json'
CACHE = CONFIG_DIR / 'nappes.cache.json'
BASE = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/'


def charger(path):
    try:
        return lire_json(path)
    except RuntimeError:
        return {}


def requete(operation, params):
    if operation not in ('stations', 'chroniques'):
        raise ValueError('operation')
    with urlopen(BASE + operation + '?' + urlencode(params), timeout=20) as response:
        raw = response.read(2_000_001)
    if len(raw)>2_000_000:
        raise ValueError('response size')
    result = json.loads(raw)
    if not isinstance(result,dict) or not isinstance(result.get('data'),list):
        raise ValueError('response format')
    return result


def normaliser_departement(saisie):
    departement=re.sub(r'\s+', '', str(saisie)).upper()
    if re.fullmatch(r'\d{5}',departement):
        # Les codes postaux corses ne permettent pas de distinguer 2A et 2B sûrement.
        if departement.startswith('20'):raise ValueError('department')
        departement=departement[:3] if departement.startswith('97') else departement[:2]
    if not re.fullmatch(r'(?:0[1-9]|[1-8]\d|9[0-5]|2[AB]|97[1-46])', departement):
        raise ValueError('department')
    return departement


def trier_stations(stations, inclure_anciennes=False, aujourd_hui=None):
    aujourd_hui=aujourd_hui or date.today()
    debut=aujourd_hui-timedelta(days=365)
    def dernier(station):
        try:return date.fromisoformat(station.get('date_fin_mesure') or '')
        except (ValueError,TypeError):return date.min
    propres=[station for station in stations if isinstance(station,dict) and station.get('code_bss')]
    if not inclure_anciennes:
        propres=[station for station in propres if debut<=dernier(station)<=aujourd_hui]
    return sorted(propres,key=dernier,reverse=True)


def rechercher(departement):
    departement=normaliser_departement(departement)
    stations=[];vus=set();incomplet=False
    # Ne suivre aucun lien de pagination arbitraire : même API, filtres constants.
    for page in range(1,11):
        resultat=requete('stations',{'code_departement':departement,'size':500,'page':page})
        nouveaux=0
        for station in resultat['data']:
            if not isinstance(station,dict) or not station.get('code_bss'):continue
            code=station['code_bss']
            if code in vus:continue
            vus.add(code);stations.append(station);nouveaux+=1
        incomplet=bool(resultat.get('next'))
        if not incomplet or not nouveaux:break
    return trier_stations(stations,True),incomplet


def erreur_lisible(error):
    if isinstance(error,HTTPError):
        return t('groundwater_http_error').format(status=error.code)
    if isinstance(error,(TimeoutError,socket.timeout)):
        return t('groundwater_timeout')
    if isinstance(error,URLError):
        if isinstance(error.reason,ssl.SSLCertVerificationError):return t('groundwater_tls_error')
        if isinstance(error.reason,(TimeoutError,socket.timeout)):return t('groundwater_timeout')
        return t('groundwater_connection_error')
    if isinstance(error,ssl.SSLCertVerificationError):return t('groundwater_tls_error')
    if isinstance(error,(ValueError,TypeError,KeyError)):return t('groundwater_format_error')
    return t('groundwater_error')


def normaliser(rows):
    propres=[]
    for row in rows:
        if not isinstance(row,dict):continue
        try:
            jour=date.fromisoformat(row.get('date_mesure',''))
        except (ValueError,TypeError):continue
        niveau=row.get('niveau_nappe_eau')
        if type(niveau) not in (int,float) or not math.isfinite(niveau):continue
        profondeur=row.get('profondeur_nappe')
        if type(profondeur) not in (int,float) or not math.isfinite(profondeur):profondeur=None
        propres.append({'date':jour.isoformat(),'niveau':niveau,'profondeur':profondeur,
                        'qualification':str(row.get('qualification') or ''),
                        'statut':str(row.get('statut') or '')})
    return sorted(propres,key=lambda r:r['date'])


def historique(station):
    if not isinstance(station,str) or not station or len(station)>100:raise ValueError('station')
    resultat=requete('chroniques',{'code_bss':station,'size':100,'sort':'desc'})
    return normaliser(resultat['data'])


PALETTE = dict(BG='#F2F6F1', CARD='#FBFDF9', TEXT='#223228', BLUE='#3F6F99', LIGHT_BLUE='#E4EEF7', BORDER='#D6E2D8')


def harmoniser(widget, palette):
    """Palette locale : ne modifie pas les styles des autres fenêtres."""
    import tkinter as tk
    from tkinter import ttk
    if isinstance(widget,ttk.Widget):
        # Native ttk controls need styles rather than bg/fg options. Keep each
        # palette separate so opening another themed window cannot recolor it.
        style=ttk.Style(widget)
        prefix='Gruterra'+palette['BG'].lstrip('#')
        if isinstance(widget,ttk.Treeview):
            name=prefix+'.Treeview'
            style.configure(name,background=palette['CARD'],fieldbackground=palette['CARD'],foreground=palette['TEXT'])
            style.configure(name+'.Heading',background=palette['BG'],foreground=palette['TEXT'])
            style.map(name,background=[('selected',palette['LIGHT_BLUE'])],foreground=[('selected',palette['BLUE'])])
            widget.configure(style=name)
        elif isinstance(widget,ttk.Combobox):
            name=prefix+'.TCombobox'
            style.configure(name,foreground=palette['TEXT'],fieldbackground=palette['CARD'],background=palette['BG'])
            style.map(name,fieldbackground=[('readonly',palette['CARD'])],foreground=[('readonly',palette['TEXT'])],selectbackground=[('readonly',palette['LIGHT_BLUE'])],selectforeground=[('readonly',palette['BLUE'])])
            widget.configure(style=name)
        for child in widget.winfo_children():harmoniser(child,palette)
        return
    if isinstance(widget, (tk.Toplevel, tk.Frame, tk.LabelFrame, tk.Label, tk.Checkbutton)):
        widget.configure(bg=palette['BG'])
        if isinstance(widget, (tk.LabelFrame, tk.Label, tk.Checkbutton)):
            widget.configure(fg=palette['TEXT'])
        if isinstance(widget, tk.Checkbutton):
            widget.configure(selectcolor=palette['CARD'], activebackground=palette['BG'], activeforeground=palette['TEXT'])
    elif isinstance(widget, tk.Button):
        widget.configure(bg=palette['LIGHT_BLUE'], fg=palette['BLUE'], activebackground=palette['CARD'], activeforeground=palette['TEXT'])
    elif isinstance(widget, tk.Entry):
        widget.configure(bg=palette['CARD'], fg=palette['TEXT'], insertbackground=palette['TEXT'])
    for child in widget.winfo_children():
        harmoniser(child, palette)


def ouvrir(parent, palette=None):
    import tkinter as tk
    from tkinter import ttk
    palette={**PALETTE, **(palette or {})}
    window=tk.Toplevel(parent);window.title(t('groundwater_title'));window.geometry('900x700');window.minsize(650,550)
    config=charger(CONFIG)
    enabled=tk.BooleanVar(value=config.get('enabled') is True)
    tk.Checkbutton(window,text=t('groundwater_enable'),variable=enabled).pack(anchor='w',padx=12,pady=8)
    tk.Label(window,text=t('groundwater_explanation'),wraplength=810,justify='left').pack(fill='x',padx=12)
    line=tk.Frame(window);line.pack(fill='x',padx=12,pady=8)
    tk.Label(line,text=t('groundwater_department')).pack(side='left')
    dept=tk.StringVar(value=config.get('department',''));tk.Entry(line,textvariable=dept,width=6).pack(side='left',padx=8)
    status=tk.StringVar(value=t('groundwater_manual'));tk.Label(window,textvariable=status,wraplength=810,justify='left').pack(fill='x',padx=12)
    toutes_stations=list(config.get('stations',[])) if isinstance(config.get('stations'),list) else []
    stations=[]
    anciennes=tk.BooleanVar(value=False)
    current=config.get('station')
    style=ttk.Style(window)
    style.configure('Groundwater.TCombobox',foreground=palette['TEXT'],fieldbackground=palette['CARD'],background=palette['BG'])
    style.map('Groundwater.TCombobox',fieldbackground=[('readonly',palette['CARD'])],foreground=[('readonly',palette['TEXT'])],selectbackground=[('readonly',palette['LIGHT_BLUE'])],selectforeground=[('readonly',palette['BLUE'])])
    select=ttk.Combobox(window,state='readonly',width=100,style='Groundwater.TCombobox')
    detail=tk.StringVar()
    def station_details():
        index=select.current()
        station=stations[index] if index>=0 else {}
        names=station.get('noms_masse_eau_edl')
        if isinstance(names,list):names=' · '.join(name for name in names if isinstance(name,str))
        detail.set(t('groundwater_aquifer').format(name=names if isinstance(names,str) and names else t('groundwater_unknown_aquifer')))
    def labels():
        nonlocal current
        code=stations[select.current()]['code_bss'] if select.current()>=0 else current
        stations[:]=trier_stations(toutes_stations,anciennes.get())
        select['values']=[f"{station.get('nom_commune','')} · {station['code_bss']} · {t('groundwater_last')}: {station.get('date_fin_mesure') or '—'}" for station in stations]
        codes=[station['code_bss'] for station in stations]
        if code in codes:select.current(codes.index(code))
        else:select.set('');current=None
        station_details()
        status.set(t('groundwater_recent_count').format(count=len(stations)) if not anciennes.get() else t('groundwater_all_count').format(count=len(stations)))
    tk.Checkbutton(window,text=t('groundwater_include_old'),variable=anciennes,command=lambda:(labels(),afficher([]))).pack(anchor='w',padx=12)
    select.pack(fill='x',padx=12,pady=6)
    labels()
    tk.Label(window,textvariable=detail,wraplength=810,justify='left').pack(fill='x',padx=12)
    canvas=tk.Canvas(window,height=180,bg=palette['CARD'],highlightbackground=palette['BORDER'],highlightthickness=1);canvas.pack(fill='x',padx=12,pady=8)
    table_frame=tk.Frame(window);table_frame.pack(fill='both',expand=True,padx=12)
    style=ttk.Style(window)
    style.configure('Groundwater.Treeview', background=palette['CARD'],fieldbackground=palette['CARD'],foreground=palette['TEXT'])
    style.configure('Groundwater.Treeview.Heading',background=palette['BG'],foreground=palette['TEXT'])
    style.map('Groundwater.Treeview',background=[('selected',palette['LIGHT_BLUE'])],foreground=[('selected',palette['BLUE'])])
    table=ttk.Treeview(table_frame,style='Groundwater.Treeview',columns=('date','level','depth','quality','status'),show='headings',height=8)
    for column,label in zip(('date','level','depth','quality','status'),('groundwater_date','groundwater_level','groundwater_depth','groundwater_quality','groundwater_validation_status')):
        table.heading(column,text=t(label));table.column(column,width=190,minwidth=130)
    bar=ttk.Scrollbar(table_frame,orient='vertical',command=table.yview);bar.pack(side='right',fill='y')
    horizontal=ttk.Scrollbar(table_frame,orient='horizontal',command=table.xview);horizontal.pack(side='bottom',fill='x')
    table.configure(yscrollcommand=bar.set,xscrollcommand=horizontal.set);table.pack(fill='both',expand=True)
    def afficher(rows):
        table.delete(*table.get_children());canvas.delete('all')
        for r in reversed(rows):table.insert('', 'end',values=(r['date'],f"{r['niveau']:g}",'—' if r['profondeur'] is None else f"{r['profondeur']:g}",r['qualification'] or '—',r.get('statut') or '—'))
        if not rows:return
        lo=min(r['niveau'] for r in rows);hi=max(r['niveau'] for r in rows)
        width=max(200,canvas.winfo_width());start=date.fromisoformat(rows[0]['date']);span=max(1,(date.fromisoformat(rows[-1]['date'])-start).days)
        points=[]
        for r in rows:
            x=35+(width-70)*(date.fromisoformat(r['date'])-start).days/span
            y=140-110*(r['niveau']-lo)/max(0.01,hi-lo)
            points.extend((x,y));canvas.create_oval(x-2,y-2,x+2,y+2,fill=palette['BLUE'])
        if len(rows)>1:canvas.create_line(*points,fill=palette['BLUE'],width=2)
        canvas.create_text(35,15,text=t("groundwater_range").format(low=f"{lo:g}",high=f"{hi:g}"),fill=palette["TEXT"],anchor='w')
        canvas.create_text(35,165,text=rows[0]['date'],fill=palette['TEXT'],anchor='w');canvas.create_text(width-35,165,text=rows[-1]['date'],fill=palette['TEXT'],anchor='e')
    displayed=[]
    original_afficher=afficher
    def afficher(rows):
        displayed[:]=rows
        original_afficher(rows)
    canvas.bind('<Configure>',lambda event:original_afficher(displayed))
    def selection_changed(event=None):
        station_details()
        afficher([])
        status.set(t('groundwater_selection_changed'))
    select.bind('<<ComboboxSelected>>',selection_changed)
    queue=Queue();busy=False
    def lancer(action,kind):
        nonlocal busy
        if busy:return
        busy=True;select.configure(state='disabled');status.set(t('groundwater_loading'))
        def worker():
            try:queue.put((kind,action(),None))
            except Exception as error:queue.put((kind,None,erreur_lisible(error)))
        threading.Thread(target=worker,daemon=True).start();window.after(100,poll)
    def poll():
        nonlocal busy, current
        try:kind,value,error=queue.get_nowait()
        except Empty:window.after(100,poll);return
        busy=False;select.configure(state='readonly')
        if error:status.set(error);return
        if kind=='stations':
            toutes_stations[:]=value[0];labels();select.set('');current=None;station_details();afficher([])
            if value[1]:status.set(status.get()+' '+t('groundwater_limited'))
        else:
            afficher(value);status.set(t('groundwater_observed') if value else t('groundwater_empty'))
            try:
                CONFIG_DIR.mkdir(parents=True,exist_ok=True);ecrire_json(CACHE,{'station':current,'rows':value})
            except (OSError,RuntimeError):status.set(t('groundwater_save_error'))
    def chercher():
        if busy:return
        try:departement=normaliser_departement(dept.get())
        except ValueError:status.set(t('groundwater_department_invalid'));return
        dept.set(departement)
        lancer(lambda:rechercher(departement),'stations')
    tk.Button(line,text=t('groundwater_search'),command=chercher).pack(side='left')
    def actualiser():
        nonlocal current
        if busy:return
        index=select.current()
        if index<0:status.set(t('groundwater_choose'));return
        current=stations[index]['code_bss']
        afficher([])  # Ne pas laisser la courbe de l'ancienne station sous la nouvelle sélection.
        station_demandee=current
        lancer(lambda:historique(station_demandee),'history')
    buttons=tk.Frame(window);buttons.pack(fill='x',padx=12,pady=10)
    tk.Button(buttons,text=t('groundwater_refresh'),command=actualiser).pack(side='left')
    def sauver():
        index=select.current();selected=stations[index]['code_bss'] if index>=0 else None
        try:
            CONFIG_DIR.mkdir(parents=True,exist_ok=True);ecrire_json(CONFIG,{'enabled':enabled.get(),'department':dept.get().strip(),'station':selected,'stations':toutes_stations})
            status.set(t('groundwater_saved'))
        except (OSError,RuntimeError):status.set(t('groundwater_save_error'))
    tk.Button(buttons,text=t('groundwater_save'),command=sauver).pack(side='right')
    def aide():
        help_window=tk.Toplevel(window);help_window.title(t('groundwater_help'));help_window.geometry('720x550')
        scrollbar=ttk.Scrollbar(help_window);scrollbar.pack(side='right',fill='y')
        text=tk.Text(help_window,wrap='word',padx=18,pady=18,bg=palette['CARD'],fg=palette['TEXT'],yscrollcommand=scrollbar.set)
        text.pack(fill='both',expand=True);scrollbar.configure(command=text.yview)
        text.insert('1.0',t('groundwater_help_text'));text.configure(state='disabled')
        harmoniser(help_window,palette)
    tk.Button(buttons,text=t('groundwater_help'),command=aide).pack(side='left',padx=10)
    harmoniser(window,palette)
    cache=charger(CACHE)
    if current and cache.get('station')==current:
        rows=cache.get('rows',[])
        # Cache produit par ce module ; ne jamais confondre sa lecture avec un rafraîchissement.
        try:afficher(rows);status.set(t('groundwater_cached'))
        except (TypeError,ValueError,KeyError):status.set(t('groundwater_empty'))


def carte(parent, palette=None):
    import tkinter as tk
    config=charger(CONFIG)
    if config.get('enabled') is not True:return
    palette={**PALETTE, **(palette or {})}
    frame=tk.LabelFrame(parent,text=t('groundwater_title'));frame.pack(fill='x',padx=20,pady=8)
    message=t('groundwater_manual')
    cache=charger(CACHE)
    if config.get('station') and cache.get('station')==config['station']:
        rows=cache.get('rows')
        if isinstance(rows,list):
            valid=[]
            for row in rows:
                if not isinstance(row,dict):continue
                try:day=date.fromisoformat(row.get('date',''))
                except (ValueError,TypeError):continue
                value=row.get('niveau')
                if type(value) in (int,float) and math.isfinite(value):valid.append((day,value))
            if valid:
                day,value=max(valid,key=lambda item:item[0])
                station=next((station for station in config.get('stations',[]) if isinstance(station,dict) and station.get('code_bss')==config['station']),{})
                name=station.get('nom_commune') or config['station']
                message=t('groundwater_home_latest').format(station=name,level=f'{value:g}',date=day.isoformat())
    tk.Label(frame,text=message,wraplength=650,justify='left').pack(side='left',padx=12,pady=8)
    tk.Button(frame,text=t('groundwater_open'),command=lambda:ouvrir(parent.winfo_toplevel(),palette)).pack(side='right',padx=12)

    harmoniser(frame,palette)

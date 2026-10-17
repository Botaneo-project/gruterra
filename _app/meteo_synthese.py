"""Sélection météo locale par mesure, sans accès réseau ni données intérieures."""
import math
from i18n import traduire_courant as t


def choisir_mesure(cle,privees,publiques,nom_public,format_nombre,unite=''):
    from capteurs.netatmo import extraire_mesures_publiques, extraire_mesures
    candidats=[]
    def ajouter(station,mesures,source,private=False):
        if private and isinstance(mesures.get('brut'),dict):
            mesures=extraire_mesures({'dashboard_data':mesures['brut']})
        valeur=mesures.get(cle)
        if type(valeur) not in (int,float) or not math.isfinite(valeur):return
        distance=station.get('distance_m')
        if type(distance) not in (int,float) or not math.isfinite(distance) or distance<0:
            # Station de l'utilisateur : source personnelle, sans distance prétendue.
            distance=0 if private else math.inf
        if not private and math.isfinite(distance):
            source=t('weather_source_distance').format(source=source,distance=round(distance))
        candidats.append({'texte':format_nombre(valeur,unite),'source':source,
                          'date':mesures.get('dates_mesures',{}).get(cle) or mesures.get('date_mesure'),
                          'distance':distance,'privee':private,'valeur':valeur,'favorite':bool(station.get('favorite'))})
    for station in privees:
        source=station.get('nom') or t('weather_personal_station')
        if cle=='pression':ajouter(station,station.get('mesures',{}),source,True)
        for module in station.get('modules',[]):
            type_requis='NAModule1' if cle in ('temperature','humidite') else 'NAModule3' if cle.startswith('pluie') else 'NAModule2'
            if module.get('type')!=type_requis:continue
            module_source=source+' · '+(module.get('nom') or t('weather_outdoor_module'))
            ajouter(station,module.get('mesures',{}),module_source,True)
    for station in publiques:
        mesures=station.get('mesures',{})
        raw=mesures.get('brut')
        if isinstance(raw,dict) and isinstance(raw.get('measures'),dict):
            mesures=extraire_mesures_publiques(raw)  # Répare aussi le cache ancien en mémoire.
        ajouter(station,mesures,nom_public(station))
    if not candidats:
        return {'texte':t('interface_text_5146'),'source':None,'etat':'absent','cle':cle,
                'explication':t('weather_rain_missing') if cle.startswith('pluie') else t('weather_measurement_missing')}
    candidats.sort(key=lambda c:(0 if c['privee'] else 1 if c['favorite'] else 2,c['distance']))
    return {**candidats[0],'etat':'ok','cle':cle}


def dessiner_picto(parent,cle,couleur,fond):
    """Petits pictogrammes vectoriels : aucune dépendance aux emojis Windows."""
    import tkinter as tk
    c=tk.Canvas(parent,width=30,height=28,bg=fond,highlightthickness=0)
    c.pack(side='left',padx=(0,5))
    def line(*points,**kw):c.create_line(*points,fill=couleur,width=2,**kw)
    if cle=='temperature':
        c.create_oval(9,17,21,27,outline=couleur,width=2)
        c.create_rectangle(12,3,18,20,outline=couleur,width=2)
        line(15,9,15,22)
    elif cle=='humidite':
        c.create_polygon(15,2,6,16,7,23,15,27,23,23,24,16,fill='',outline=couleur,width=2,smooth=True)
    elif cle=='pression':
        c.create_oval(3,3,27,27,outline=couleur,width=2);line(15,15,22,8);line(7,21,23,21)
    elif cle.startswith('pluie'):
        c.create_oval(8,3,23,17,outline=couleur,width=2);line(4,16,27,16)
        for x in (8,16,24):line(x,20,x-3,26)
    elif cle=='direction_vent':
        c.create_oval(3,2,27,26,outline=couleur,width=2)
        c.create_polygon(15,4,10,20,15,17,20,20,fill=couleur)
    else:
        line(2,8,23,8,27,5,25,2,smooth=True);line(2,15,24,15)
        line(5,22,22,22,26,25,smooth=True)
    return c

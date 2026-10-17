"""Recherche explicite de communes ; ne modifie aucune localisation privée."""
import re,math
import requests

def postcode(value):
    code=re.sub(r'\s+','',str(value))
    if not re.fullmatch(r'\d{5}',code):raise ValueError('weather_postcode_invalid')
    return code

def normalise(data,code):
    if not isinstance(data,list):raise ValueError('weather_towns_invalid')
    result=[]
    for town in data:
        if not isinstance(town,dict) or code not in town.get('codesPostaux',[]):continue
        center=town.get('centre',{})
        coordinates=center.get('coordinates') if isinstance(center,dict) else None
        if not isinstance(coordinates,list) or len(coordinates)!=2:continue
        longitude,latitude=coordinates
        if any(type(value) not in (int,float) or not math.isfinite(value) for value in coordinates):continue
        if not -180<=longitude<=180 or not -90<=latitude<=90:continue
        if not isinstance(town.get('nom'),str) or not isinstance(town.get('code'),str):continue
        result.append({'name':town['nom'],'code':town['code'],'latitude':latitude,'longitude':longitude})
    return sorted(result,key=lambda town:(town['name'],town['code']))

def search(value):
    code=postcode(value)
    response=requests.get('https://geo.api.gouv.fr/communes',params={'codePostal':code,'fields':'nom,code,centre,codesPostaux','format':'json'},timeout=15,allow_redirects=False)
    if response.status_code!=200 or len(response.content)>1_000_000:raise ValueError('weather_towns_unavailable')
    return normalise(response.json(),code)

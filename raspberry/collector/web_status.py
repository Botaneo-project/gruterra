"""Authenticated mobile dashboard with queued collection requests."""
try:
    from installation_paths import installation_root
except ModuleNotFoundError:
    # Running this utility directly from the source checkout.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from installation_paths import installation_root
import json
import base64
import hashlib
import hmac
import secrets
import threading
import sqlite3
from urllib.parse import urlsplit
from pi_web_i18n import language, render, EN
from light_schedule import load as load_lamp, save as save_lamp, analyse_profile as analyse_lamp
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = installation_root()


def weather_snapshot(path):
    """Read only; include confirmed observations and preserve source values."""
    if not path.exists():
        return {'rows': [], 'total': 0}
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
    try:
        total = db.execute('SELECT count(*) FROM weather_outbox_v1').fetchone()[0]
        rows = []
        for raw, confirmed in db.execute('SELECT row_json, confirmed FROM weather_outbox_v1 ORDER BY sequence DESC LIMIT 300'):
            row = json.loads(raw)
            o = row['observation']
            rows.append({'observation': {k: o.get(k) for k in ('station_id', 'module_id', 'source', 'api_field', 'value', 'unit', 'source_time', 'period')},
                         'retrieved_at': row['retrieved_at'], 'confirmed': bool(confirmed)})
        return {'rows': rows, 'total': total}
    finally:
        db.close()


WEATHER_HTML = '''<!doctype html><html lang="fr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Gruterra · Historique météo</title><style>
*{box-sizing:border-box}body{margin:0;background:#eff4ef;color:#223228;font:17px system-ui}main{max-width:650px;margin:auto;padding:24px 18px}h1{color:#24583b;font-size:30px}a{color:#24583b}article,.notice{background:white;border:1px solid #dde7dc;border-radius:16px;padding:18px;margin:14px 0}p{line-height:1.5;overflow-wrap:anywhere}.muted{font-size:14px;color:#58665a}.value{font-size:26px;font-weight:650}button,select{font:inherit;min-height:48px;width:100%;border-radius:10px;padding:10px;margin:8px 0}button{background:#326b47;color:white;border:0}select{background:white;border:1px solid #b7cdbb}h2{font-size:18px}button:focus-visible,a:focus-visible,select:focus-visible{outline:3px solid #bd7c20;outline-offset:3px}
</style><main><a href="/">← Retour aux capteurs</a><h1>Historique météo</h1>
<p class="notice">Relevés conservés sur ce Raspberry. Les cumuls de pluie ne sont pas additionnés. Plusieurs versions d’une mesure peuvent apparaître.</p>
<label for="station">Station</label><select id="station"><option value="">Toutes les stations</option></select>
<label for="measure">Mesure</label><select id="measure"><option value="">Toutes les mesures</option></select>
<label for="range">Période de mesure</label><select id="range"><option value="0">Tout l’historique disponible</option><option value="1">Dernières 24 heures</option><option value="7">7 derniers jours</option><option value="30">30 derniers jours</option></select>
<p id="count" class="muted" aria-live="polite"></p><button id="refresh">Actualiser l’historique</button><p id="state" role="status">Chargement…</p><div id="rows"></div>
<p class="muted">Actualiser consulte le stockage local sans lancer de collecte Netatmo. Les dates sont affichées dans le fuseau du téléphone. Une station voisine ne mesure pas exactement la pluie chez vous.</p></main>
<script>
const el=id=>document.getElementById(id);let rows=[];
function node(tag,text,cls){const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n}
function date(v){return v?new Date(v).toLocaleString('fr-FR'):'Date inconnue'}
const labels={rain_60min:'Pluie · cumul sur 1 heure',rain_24h:'Pluie · cumul sur 24 heures',sum_rain_1:'Pluie · cumul source 1 h',sum_rain_24:'Pluie · cumul source 24 h',rain_live:'Pluie · mesure source',Rain:'Pluie',Temperature:'Température',temperature:'Température',Humidity:'Humidité',humidity:'Humidité',Pressure:'Pression',pressure:'Pression',WindStrength:'Vitesse du vent',wind_strength:'Vitesse du vent'};
function render(){el('rows').replaceChildren();const days=Number(el('range').value);const shown=rows.filter(r=>(!el('station').value||r.observation.station_id===el('station').value)&&(!el('measure').value||r.observation.api_field===el('measure').value)&&(!days||(r.observation.source_time&&Date.parse(r.observation.source_time)>=Date.now()-days*86400000&&Date.parse(r.observation.source_time)<=Date.now())));
el('count').textContent=rows.length?shown.length+' version(s) correspondant aux filtres, parmi les '+rows.length+' dernières versions chargées.':'';
for(const r of shown){const o=r.observation,c=node('article',''),p=o.period||{};
c.append(node('h2',labels[o.api_field]||o.api_field||'Mesure'),node('p',(o.value===null||o.value===undefined?'Donnée absente':o.value)+' '+(o.unit||''),'value'),node('p','Mesurée : '+date(o.source_time)),node('p','Station : '+o.station_id+' · '+(o.source==='netatmo_public'?'Publique':'Personnelle'),'muted'));
const period=p.kind==='rolling'?'Cumul glissant'+(p.duration_seconds?' · '+p.duration_seconds/3600+' h':''):p.kind==='instant'?'Mesure instantanée':p.kind==='calendar_day'?'Journée civile':'Période non précisée';
c.append(node('p',period,'muted'));if(p.start||p.end)c.append(node('p','Du '+date(p.start)+' au '+date(p.end),'muted'));
c.append(node('p','Récupérée : '+date(r.retrieved_at)+' · '+(r.confirmed?'Réception PC confirmée':'En attente de confirmation PC'),'muted'));if(o.module_id)c.append(node('p','Module : '+o.module_id,'muted'));el('rows').append(c)}
if(rows.length&&!shown.length)el('rows').append(node('p','Aucun relevé ne correspond aux filtres. Essayez une autre période ou une autre mesure.'))}
async function refresh(){el('refresh').disabled=true;try{const response=await fetch('/api/weather',{cache:'no-store',signal:AbortSignal.timeout(12000)});if(!response.ok)throw Error();const d=await response.json();rows=d.rows;const selected=el('station').value;el('station').replaceChildren(new Option('Toutes les stations',''));for(const s of [...new Set(rows.map(r=>r.observation.station_id))])el('station').add(new Option(s,s));el('station').value=selected;
const chosen=el('measure').value;el('measure').replaceChildren(new Option('Toutes les mesures',''));for(const field of [...new Set(rows.map(r=>r.observation.api_field))])el('measure').add(new Option(labels[field]||field,field));el('measure').value=chosen;
for(const id of ['station','measure','range'])el(id).disabled=!rows.length;
if(!rows.length){el('station').replaceChildren(new Option('Aucune station enregistrée',''));el('measure').replaceChildren(new Option('Aucune mesure enregistrée',''));}
el('state').textContent=rows.length?rows.length+' version(s) affichée(s) sur '+d.total+' enregistrée(s), par ordre de stockage récent.':'Votre historique météo est vide. Les stations et les filtres seront disponibles après le premier relevé. Actualiser ne déclenche pas de collecte : son accès Netatmo doit être configuré et validé.';render()}catch(e){el('state').textContent='Historique indisponible. Vérifiez la connexion au Raspberry puis réessayez. Les données éventuellement affichées ne sont plus actualisées.'}finally{el('refresh').disabled=false}}
el('station').onchange=render;el('measure').onchange=render;el('range').onchange=render;el('refresh').onclick=refresh;refresh();
</script></html>'''



def daily_summary(db, sensor, now=None):
    now = now or datetime.now(timezone.utc)
    start = now.astimezone(ZoneInfo('Europe/Paris')).replace(hour=0, minute=0, second=0, microsecond=0)
    selected = []
    source = 'history'
    for table, quality in [('history_measurements', 'estimated_from_sensor_clock'), ('measurements', 'ntp')]:
        selected = []
        for row in db.execute('SELECT measured_at, illuminance_lux, temperature_c, moisture_percent FROM '+table+' WHERE sensor_id=? AND time_quality=? AND measured_at IS NOT NULL AND measured_at>=?', (sensor, quality, start.astimezone(timezone.utc).strftime('%Y-%m-%d'))):
            try:
                at = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
                if at.tzinfo and start <= at <= now:
                    selected.append((at, *row[1:]))
            except (ValueError, TypeError):
                continue
        if selected:
            break
        source = 'live'
    selected.sort(key=lambda r:r[0])
    if not selected:
        return {'count': 0}
    return {'count':len(selected), 'source':source, 'first':selected[0][0].isoformat(), 'last':selected[-1][0].isoformat(),
            'light_mean':sum(r[1] for r in selected)/len(selected), 'light_max':max(r[1] for r in selected),
            'temperature_mean':sum(r[2] for r in selected)/len(selected), 'moisture_mean':sum(r[3] for r in selected)/len(selected)}

def sensor_names():
    try:
        names = json.loads((BASE/'config/sensor-names.json').read_text())
        return names if isinstance(names, dict) else {}
    except (OSError, ValueError):
        return {}


def light_history(db, sensor, now=None):
    now = now or datetime.now(timezone.utc)
    start = now.astimezone(ZoneInfo('Europe/Paris')).replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff = start - timedelta(days=6)
    points = []
    source = 'history'
    for table, quality in [('history_measurements','estimated_from_sensor_clock'),('measurements','ntp')]:
        for at, lux, temperature, moisture in db.execute('SELECT measured_at,illuminance_lux,temperature_c,moisture_percent FROM '+table+' WHERE sensor_id=? AND time_quality=? AND measured_at>=? ORDER BY measured_at', (sensor,quality,cutoff.astimezone(timezone.utc).isoformat())):
            try:
                dt = datetime.fromisoformat(at.replace('Z','+00:00'))
                if dt.tzinfo and cutoff <= dt <= now and lux is not None:
                    points.append({'at':dt.isoformat(),'lux':lux,'temperature':temperature,'moisture':moisture})
            except (ValueError,TypeError):
                continue
        if points:
            break
        source = 'live'
    return {'points':points, 'source':source, 'today':start.isoformat(), 'yesterday':(start-timedelta(days=1)).isoformat(), 'week':cutoff.isoformat(), 'now':now.isoformat()}



FORECAST_LOCK = threading.Lock()
FORECAST_RETRY = 0

def forecast():
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
    import time
    import os
    global FORECAST_RETRY
    with FORECAST_LOCK:
        cache = BASE/'data/forecast.json'
        try:
            saved = json.loads(cache.read_text())
        except (OSError, ValueError):
            saved = {'rows': [], 'retrieved_at': None}
        now = time.time()
        age = now - saved.get('fetched_epoch', 0)
        if age < 3600:
            return dict(saved, stale=False)
        if now < FORECAST_RETRY:
            return dict(saved, stale=True)
        FORECAST_RETRY = now + 300
        try:
            config = json.loads((BASE/'config/forecast.json').read_text())
            lat, lon = float(config['latitude']), float(config['longitude'])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise ValueError('location')
            fields = ['temperature_2m','relative_humidity_2m','precipitation','wind_speed_10m','wind_gusts_10m']
            params = dict(latitude=lat, longitude=lon, hourly=','.join(fields), forecast_days=2, timezone='UTC', timeformat='unixtime', models='meteofrance_arome_france', wind_speed_unit='kmh', precipitation_unit='mm', temperature_unit='celsius')
            req = Request('https://api.open-meteo.com/v1/meteofrance?'+urlencode(params), headers={'User-Agent':'Gruterra/1.0'})
            with urlopen(req, timeout=12) as response:
                data = json.loads(response.read(2000000))
            h = data['hourly']
            expected = {'temperature_2m':'°C','relative_humidity_2m':'%','precipitation':'mm','wind_speed_10m':'km/h','wind_gusts_10m':'km/h'}
            if any(data['hourly_units'].get(k)!=v for k,v in expected.items()):
                raise ValueError('units')
            rows = []
            for i, at in enumerate(h['time']):
                if now < at <= now+24*3600:
                    rows.append(dict(at=at, **{k:h[k][i] for k in fields}))
            if not rows:
                raise ValueError('empty')
            result = dict(rows=rows, retrieved_at=datetime.now(timezone.utc).isoformat(), fetched_epoch=now)
            tmp = cache.with_suffix('.tmp')
            tmp.write_text(json.dumps(result))
            os.chmod(tmp, 0o600)
            os.replace(tmp, cache)
            return dict(result, stale=False)
        except Exception:
            return dict(saved, stale=True)


def day_rows(db, sensor):
    start=datetime.now(timezone.utc).astimezone(ZoneInfo('Europe/Paris')).replace(hour=0,minute=0,second=0,microsecond=0)
    result=[]
    for table in ('history_measurements','measurements'):
        for row in db.execute('SELECT measured_at,time_quality,temperature_c,moisture_percent,illuminance_lux,conductivity_us_cm FROM '+table+' WHERE sensor_id=? AND measured_at>=?',(sensor,(start-timedelta(days=1)).isoformat())):
            try:
                at=datetime.fromisoformat(row[0].replace('Z','+00:00'))
                if at.tzinfo and start<=at<=datetime.now(timezone.utc):result.append(dict(at=row[0],quality=row[1],temperature=row[2],moisture=row[3],lux=row[4],conductivity=row[5],source=table))
            except (ValueError,TypeError):pass
    return sorted(result,key=lambda r:r['at'])

def snapshot(path):
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        sensors = []
        names = sensor_names()
        for status in db.execute('SELECT * FROM sensor_status ORDER BY sensor_id'):
            row = db.execute('SELECT * FROM measurements WHERE sensor_id=? ORDER BY rowid DESC LIMIT 1',
                             (status['sensor_id'],)).fetchone()
            sensors.append({'status': dict(status), 'latest': dict(row) if row else None, 'name':names.get(status['sensor_id']), 'daily':daily_summary(db,status['sensor_id']), 'light':light_history(db,status['sensor_id']), 'lamp':load_lamp(BASE/'config/light-schedules.json',status['sensor_id']), 'lamp_groups':analyse_lamp(light_history(db,status['sensor_id'])['points'],load_lamp(BASE/'config/light-schedules.json',status['sensor_id'])) if load_lamp(BASE/'config/light-schedules.json',status['sensor_id']) else [], 'day_rows':day_rows(db,status['sensor_id'])})
        pending = sum(db.execute(f"SELECT COUNT(*) FROM {table} WHERE sync_state='pending'").fetchone()[0]
                      for table in ('measurements', 'history_measurements'))
        history = db.execute('SELECT COUNT(*) FROM history_measurements').fetchone()[0]
        return {'sensors': sensors, 'pending': pending, 'history': history,
                'checked_at': datetime.now(timezone.utc).isoformat()}
    finally:
        db.close()


HTML = '''<!doctype html><html lang="fr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Gruterra · Raspberry</title><style>
body{font:17px system-ui;margin:0;background:#f2f6f1;color:#223228}main{max-width:650px;margin:auto;padding:24px 18px}
h1{margin-bottom:4px}p{line-height:1.5}.card{background:white;padding:20px;border-radius:18px;margin:16px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.value{font-size:27px;font-weight:650}
.muted{color:#58665a;font-size:14px}button{background:#326b47;color:white;border:0;border-radius:12px;padding:14px;font:inherit;width:100%}
.warning{color:#93421c}h2{font-size:20px}
*{box-sizing:border-box}body{background:#eff4ef}main{padding:24px 18px calc(28px + env(safe-area-inset-bottom))}
h1{font-size:34px;letter-spacing:-1.2px;color:#24583b}.card{border:1px solid #dde7dc;box-shadow:0 4px 16px #183e2210}
.grid{gap:10px}.grid>div{background:#f3f7f2;padding:14px 10px;border-radius:12px;min-width:0}.value{font-size:clamp(20px,6vw,27px);overflow-wrap:anywhere}
button{min-height:50px;font-weight:650;cursor:pointer;touch-action:manipulation}button:disabled{background:#dce5dc;color:#435447;cursor:wait}
button:focus-visible{outline:3px solid #bd7c20;outline-offset:3px}#refresh{background:white;color:#326b47;border:1px solid #b7cdbb}
#connection{font-size:14px;padding:10px 12px;background:#e0eddf;border-radius:12px}#connection.offline{background:#fff0d9;color:#794600}
#collect-state{min-height:48px;font-size:15px}h2{overflow-wrap:anywhere}.badge{display:inline-block;padding:5px 9px;border-radius:8px;background:#e0eddf;color:#24583b;font-size:13px}.badge.warning{background:#fff0d9;color:#794600}
details{margin-top:15px;font-size:14px}summary{padding:10px 0;cursor:pointer;color:#536459}.warning{line-height:1.5}
@media(prefers-reduced-motion:no-preference){button{transition:background .2s}}
.forecast-overview{padding:14px 0}.forecast-range{font-size:36px;font-weight:700;color:#24583b}.forecast-strip{display:flex;overflow-x:auto;gap:8px;padding:4px 0 12px;scroll-snap-type:x proximity}.forecast-hour{flex:0 0 88px;width:88px;background:#f3f7f2;color:#223228;border:1px solid #dce5dc;display:flex;flex-direction:column;gap:9px;font-size:14px;scroll-snap-align:start}.forecast-hour strong{font-size:22px}.forecast-hour[aria-pressed=true]{border:2px solid #326b47;background:#e0eddf}.forecast-rain{color:#2873a2}.forecast-detail{background:#f3f7f2;padding:14px;border-radius:12px;font-size:14px}.forecast-detail p{margin:8px 0}.forecast-day{font-size:12px;font-weight:400}.forecast-stale{background:#fff0d9;color:#794600;padding:12px;border-radius:10px}.forecast-fresh{color:#58665a;font-size:14px}</style><main><h1>Gruterra</h1>
<p class="muted">Votre collecteur Raspberry</p><p id="connection" role="status">Chargement…</p>
<p class="card"><a href="/weather" style="color:#24583b">Consulter l’historique météo →</a></p>
<section class="card"><h2>Prévisions Météo-France</h2><p class="muted">Modèle AROME France via <a href="https://open-meteo.com/">Open-Meteo</a> · lieu configuré dans Gruterra, même en déplacement.</p><button id="forecast-load">Afficher / actualiser la météo</button><p id="forecast-state" role="status"></p><div id="forecast-rows"></div><p class="muted">Prévisions, pas observations. Pluie : cumul prévu sur l’heure précédant l’échéance affichée. La première période peut être en partie écoulée. Cache renouvelé à la consultation, au plus une fois par heure.</p></section>
<button id="collect">Lire les capteurs maintenant</button><p id="collect-state" aria-live="polite"></p><div id="sensors"></div><section class="card"><h2>Synchronisation PC</h2><p id="pending">—</p>
<p class="muted">Les relevés restent conservés sur le Raspberry. Le PC les récupère lorsque Gruterra est ouvert et que les deux appareils peuvent communiquer.</p></section>
<button id="refresh">Actualiser l’affichage</button><p class="muted">Actualiser affiche les données déjà enregistrées. « Lire les capteurs » demande une nouvelle lecture, qui peut prendre plusieurs minutes. Actualisation automatique tant que cette page est visible.</p></main>
<script>
const byId=id=>document.getElementById(id);
function element(tag,text,cls){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e}
function date(value){return value?new Date(value).toLocaleString('fr-FR'):'Aucune'}
function age(value){const n=Date.now()-new Date(value).getTime();if(!value||!Number.isFinite(n)||n<0)return 'Date à vérifier';const m=Math.floor(n/60000);return m<1?'À l’instant':m<60?'Il y a '+m+' min':m<1440?'Il y a '+Math.floor(m/60)+' h':'Il y a '+Math.floor(m/1440)+' j'}
function lampPanel(sensor){
const panel=element('section',''),settings=sensor.lamp||{start:'09:50',end:'15:50'};panel.append(element('h2','Historique pendant l’éclairage'));
const begin=document.createElement('input'),end=document.createElement('input');begin.type=end.type='time';begin.value=settings.start;end.value=settings.end;
for(const [label,input] of [['Allumage',begin],['Extinction',end]]){const l=element('label',label+' ');input.style.cssText='font:inherit;min-height:44px;margin:8px';l.append(input);panel.append(l)}
const save=element('button','Enregistrer les horaires'),state=element('p',sensor.lamp?'Horaires enregistrés sur le Pi.':'Horaires proposés, à enregistrer.','muted');panel.append(save,state);
save.onclick=async()=>{save.disabled=true;try{const r=await fetch('/api/lamp',{method:'POST',headers:{'Content-Type':'application/json','X-Botaneo-Token':'CSRF_PLACEHOLDER'},body:JSON.stringify({sensor:sensor.status.sensor_id,start:begin.value,end:end.value})});if(!r.ok)throw Error();document.activeElement.blur();await refresh()}catch(e){state.textContent='Enregistrement impossible : vérifiez les heures et la connexion.'}finally{save.disabled=false}};
const groups={},windows={};const start=settings.start,stop=settings.end;for(const g of sensor.lamp_groups||[]){groups[g.day]=g.points;windows[g.day]=g.start+'–'+g.end}
for(const day of Object.keys(groups).sort().reverse()){const rows=groups[day],values=rows.map(p=>p.lux),mean=values.reduce((a,b)=>a+b,0)/values.length;const detail=element('details','');detail.append(element('summary',day+' · '+windows[day]+' · moyenne '+Math.round(mean)+' lux · '+rows.length+' relevé(s)'),element('p','Minimum '+Math.min(...values)+' lux · maximum '+Math.max(...values)+' lux'));for(const p of rows)detail.append(element('p',date(p.at)+' · '+p.lux+' lux','muted'));panel.append(detail)}
if(Object.keys(groups).length)panel.append(lightChart({...sensor,light:{...sensor.light,points:Object.values(groups).flat()}}));
if(!Object.keys(groups).length)panel.append(element('p','Aucun relevé dans la plage choisie.'));
panel.append(element('p','Heures de Paris · 7 derniers jours disponibles. Zéros inclus, sans interpolation. Changements datés par jour d’allumage ; les jours précédents conservent leur plage. Horaires partagés avec le PC.','muted'));
const copy=element('button','Copier les données du jour'),text=document.createElement('textarea');text.readOnly=true;text.style.cssText='width:100%;min-height:180px;font:14px monospace';text.hidden=true;text.setAttribute('aria-label','Données journalières à copier');panel.append(copy,text);
copy.onclick=async()=>{const rows=sensor.day_rows;const lines=[sensor.name||sensor.status.sensor_id,'Relevés du jour — heures de Paris','Éclairage prévu : '+start+'–'+stop,'Les deux sources sont listées séparément ; elles peuvent se chevaucher.','Date et heure;Source;Qualité date;Température °C;Humidité sol %;Lumière lux;Conductivité µS/cm'];for(const day of Object.keys(groups).sort().reverse().slice(0,1)){const pts=groups[day];lines.splice(3,0,'Dernier bilan éclairage '+day+' ('+windows[day]+') : moyenne '+(pts.reduce((a,p)=>a+p.lux,0)/pts.length).toFixed(1)+' lux, '+pts.length+' relevés')}for(const p of rows)lines.push([new Date(p.at).toLocaleString('fr-FR',{timeZone:'Europe/Paris'}),p.source,p.quality,p.temperature,p.moisture,p.lux,p.conductivity].map(v=>v===null||v===undefined?'absent':v).join(';'));if(!rows.length)lines.push('Aucun relevé aujourd’hui.');text.value=lines.join('\\n');text.hidden=false;try{await navigator.clipboard.writeText(text.value);state.textContent='Données copiées.'}catch(e){text.focus();text.select();state.textContent='Appuyez longuement dans le texte, puis choisissez Copier.'}};
return panel;}

const chartRanges=new Map(),chartMetrics=new Map();
function lightChart(sensor){
 const section=element('section',''),title=element('h2','Évolution des mesures'),select=document.createElement('select');
 select.setAttribute('aria-label','Période du graphique de lumière');select.style.cssText='font:inherit;padding:12px;width:100%;min-height:48px;border-radius:10px';
 for(const [v,t] of [['today','Aujourd’hui'],['yesterday','Hier'],['week','7 jours']])select.add(new Option(t,v));
 select.value=chartRanges.get(sensor.status.sensor_id)||'today';
 const metric=document.createElement('select');metric.setAttribute('aria-label','Mesure du graphique');metric.style.cssText=select.style.cssText;for(const [v,t] of [['lux','Lumière'],['temperature','Température'],['moisture','Humidité du sol']])metric.add(new Option(t,v));metric.value=chartMetrics.get(sensor.status.sensor_id)||'lux';
 const host=element('div',''),detail=element('p','Touchez un point pour voir sa valeur.','muted');detail.setAttribute('aria-live','polite');
 section.append(title,metric,select,host,detail,element('p','Heures de Paris · dates estimées pour l’historique du capteur. Une coupure de plus de 90 minutes interrompt la courbe. Les points représentent uniquement les mesures disponibles.','muted'));
 function draw(){host.replaceChildren();const d=sensor.light;if(!d){host.append(element('p','Historique indisponible.'));return}
 const key=metric.value,unit=key==='lux'?'lux':key==='temperature'?'°C':'%',value=p=>p[key];
 const begin=Date.parse(d[select.value]),end=Date.parse(select.value==='yesterday'?d.today:d.now);
 const points=d.points.filter(p=>Number.isFinite(value(p))&&Date.parse(p.at)>=begin&&(select.value==='yesterday'?Date.parse(p.at)<end:Date.parse(p.at)<=end)).sort((a,b)=>Date.parse(a.at)-Date.parse(b.at));
 detail.textContent=points.length+' relevé(s) · '+(d.source==='history'?'historique du capteur':'lectures ponctuelles');
 if(!points.length){host.append(element('p','Aucun relevé pour cette période.'));return}
 const NS='http://www.w3.org/2000/svg',svg=document.createElementNS(NS,'svg');svg.setAttribute('viewBox','0 0 600 260');svg.style.cssText='width:100%;height:auto;display:block';svg.setAttribute('role','group');svg.setAttribute('aria-label',metric.selectedOptions[0].text+' en '+unit);
 function shape(tag,attrs,text){const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;svg.append(n);return n}
 const min=key==='temperature'?Math.min(0,...points.map(value)):0,max=key==='moisture'?100:Math.max(1,...points.map(value)),span=max-min,x=p=>58+(Date.parse(p.at)-begin)/Math.max(1,end-begin)*520,y=p=>215-(value(p)-min)/span*185;
 for(let i=0;i<3;i++){const yy=215-i*92.5;shape('line',{x1:58,x2:578,y1:yy,y2:yy,stroke:'#dce5dc'});shape('text',{x:52,y:yy+4,'text-anchor':'end','font-size':12,fill:'#58665a'},(min+span*i/2).toLocaleString('fr-FR',{maximumFractionDigits:1}))}
 shape('text',{x:58,y:16,'font-size':12,fill:'#58665a'},unit);
 const fmt=t=>new Date(t).toLocaleString('fr-FR',{timeZone:'Europe/Paris',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
 shape('text',{x:58,y:245,'font-size':12,fill:'#58665a'},fmt(begin));shape('text',{x:578,y:245,'font-size':12,'text-anchor':'end',fill:'#58665a'},fmt(end));
 let previous=null;for(const p of points){if(previous&&Date.parse(p.at)-Date.parse(previous.at)<=90*60000)shape('line',{x1:x(previous),y1:y(previous),x2:x(p),y2:y(p),stroke:'#326b47','stroke-width':2});
 const label=fmt(p.at)+' · '+value(p).toLocaleString('fr-FR',{maximumFractionDigits:1})+' '+unit;const dot=shape('circle',{cx:x(p),cy:y(p),r:5,fill:'#326b47',tabindex:0,role:'button','aria-label':label});dot.onclick=()=>detail.textContent=label;dot.onfocus=()=>detail.textContent=label;dot.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();detail.textContent=label}};previous=p}
 host.append(svg);svg.onclick=e=>{const r=svg.getBoundingClientRect(),pos=(e.clientX-r.left)/r.width*600;const nearest=points.reduce((a,b)=>Math.abs(x(a)-pos)<Math.abs(x(b)-pos)?a:b);detail.textContent=fmt(nearest.at)+' · '+value(nearest).toLocaleString('fr-FR',{maximumFractionDigits:1})+' '+unit};
 }
 metric.onchange=()=>{chartMetrics.set(sensor.status.sensor_id,metric.value);draw()};select.onchange=()=>{chartRanges.set(sensor.status.sensor_id,select.value);draw()};draw();return section;
}

let refreshing=false;

async function refresh(){if(refreshing)return;refreshing=true;try{
const r=await fetch('/api/status',{cache:'no-store',signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error();const data=await r.json();
byId('connection').className='';byId('connection').textContent='Raspberry joignable · '+date(data.checked_at);
byId('collect').disabled=Boolean(data.collection.running||data.collection.pending);
byId('collect').textContent=data.collection.running?'Lecture en cours…':data.collection.pending?'Demande en attente…':'Lire les capteurs maintenant';
byId('collect-state').textContent=data.collection.running?'Le Raspberry lit les capteurs. Les valeurs précédentes restent visibles.':data.collection.pending?'Demande reçue. En attente du collecteur…':data.collection.message+(data.collection.finished_at?' · '+date(data.collection.finished_at):'');
const expanded=new Set([...byId('sensors').querySelectorAll('details[open]')].map(e=>e.dataset.sensor));
byId('sensors').replaceChildren();
for(const sensor of data.sensors){const s=sensor.status,m=sensor.latest,c=element('section','','card');
c.append(element('h2',sensor.name||'Capteur '+(data.sensors.indexOf(sensor)+1)));const old=!m||m.time_quality!=='ntp'||Date.now()-new Date(m.measured_at).getTime()>12*3600000;c.append(element('p',m?age(m.measured_at):'En attente de première mesure','badge'+(old?' warning':'')));
if(m){const grid=element('div','','grid');
for(const [label,value,unit] of [['Température',m.temperature_c,'°C'],['Humidité du sol',m.moisture_percent,'%'],['Lumière',m.illuminance_lux,'lux'],['Conductivité',m.conductivity_us_cm,'µS/cm']]){
const cell=element('div','');cell.append(element('div',label,'muted'),element('div',(typeof value==='number'?value.toLocaleString('fr-FR',{maximumFractionDigits:1}):'—')+' '+unit,'value'));grid.append(cell)}c.append(grid);
c.append(element('p','Dernier relevé : '+date(m.measured_at),'muted'));
if(m.time_quality!=='ntp')c.append(element('p','Date non confirmée : horloge du Raspberry à vérifier.','warning'));
else if(Date.now()-new Date(m.measured_at).getTime()>12*3600000)c.append(element('p','Relevé ancien : plus de 12 heures.','warning'));
}else c.append(element('p','Aucune mesure disponible.'));
const day=sensor.daily;c.append(element('h2','Aujourd’hui · lumière et moyennes'));
if(day&&day.count){const grid=element('div','','grid');for(const [label,value,unit] of [['Lumière moyenne mesurée',day.light_mean,'lux'],['Maximum mesuré',day.light_max,'lux'],['Température moyenne',day.temperature_mean,'°C'],['Humidité du sol moyenne',day.moisture_mean,'%']]){const cell=element('div','');cell.append(element('div',label,'muted'),element('div',value.toLocaleString('fr-FR',{maximumFractionDigits:1})+' '+unit,'value'));grid.append(cell)}c.append(grid,element('p',day.count+' relevé(s) · du '+date(day.first)+' au '+date(day.last),'muted'),element('p','Journée définie en heure de Paris. Moyennes des relevés disponibles, nuit comprise : elles ne représentent pas nécessairement toute la journée. '+(day.source==='history'?'Historique du capteur, dates estimées depuis son horloge.':'Lectures ponctuelles uniquement.'),'muted'));}else c.append(element('p','Pas encore de relevé daté pour aujourd’hui.','muted'));
c.append(lightChart(sensor),lampPanel(sensor));
if(s.last_error)c.append(element('p','Dernière collecte en échec. Les dernières valeurs sont conservées.','warning'));
const details=element('details','');details.dataset.sensor=s.sensor_id;details.open=expanded.has(s.sensor_id);details.append(element('summary','Détails du capteur'),element('p',s.sensor_id),element('p','Dernière tentative : '+date(s.last_attempt)),element('p','Dernière réussite : '+date(s.last_success)));c.append(details);byId('sensors').append(c)}
if(!data.sensors.length)byId('sensors').append(element('p','Aucun capteur enregistré.'));
byId('pending').textContent=data.pending+' relevé(s) en attente de confirmation du PC · '+data.history+' relevé(s) historiques conservés.';
}catch(e){byId('connection').className='offline';byId('connection').textContent='Connexion interrompue · les valeurs affichées ne sont plus actualisées.';byId('collect').disabled=true}finally{refreshing=false}}
function renderForecast(rows){
 const host=byId('forecast-rows');host.replaceChildren();
 if(!rows.length){host.append(element('p','Aucune échéance future disponible.'));return}
 const valid=v=>typeof v==='number'&&Number.isFinite(v);
 const number=(v,u)=>valid(v)?v.toLocaleString('fr-FR',{maximumFractionDigits:1})+' '+u:'—';
 const dayLabel=p=>{const day=new Date(p.at*1000),today=new Date(),tomorrow=new Date();tomorrow.setDate(today.getDate()+1);return day.toDateString()===today.toDateString()?'Aujourd’hui':day.toDateString()===tomorrow.toDateString()?'Demain':day.toLocaleDateString('fr-FR',{day:'2-digit',month:'2-digit'})};
 const hour=p=>new Date(p.at*1000).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
 const temperatures=rows.map(p=>p.temperature_2m).filter(valid);
 const top=element('div','','forecast-overview');
 top.append(element('div','Prochaines 24 heures','muted'),element('div',temperatures.length?number(Math.min(...temperatures),'°')+' — '+number(Math.max(...temperatures),'°'):'—','forecast-range'));
 top.append(element('p','Températures prévues · minimum / maximum','muted'));host.append(top);
 const strip=element('div','','forecast-strip');strip.setAttribute('aria-label','Prévisions heure par heure');
 const detail=element('div','','forecast-detail');detail.setAttribute('aria-live','polite');
 function select(p){detail.replaceChildren(element('strong',dayLabel(p)+' · '+hour(p)),element('p','Température'+' : '+number(p.temperature_2m,'°C')+' · '+'Pluie prévue sur 1 h'+' : '+number(p.precipitation,'mm')),element('p','Période de pluie : '+hour({at:p.at-3600})+'–'+hour(p),'muted'),element('p','Vent'+' : '+number(p.wind_speed_10m,'km/h')+' · '+'Rafales'+' : '+number(p.wind_gusts_10m,'km/h')),element('p','Humidité de l’air'+' : '+number(p.relative_humidity_2m,'%')));for(const b of strip.children)b.setAttribute('aria-pressed',String(b.dataset.at===String(p.at)))}
 for(const p of rows){const b=element('button','','forecast-hour');b.type='button';b.dataset.at=p.at;b.setAttribute('aria-pressed','false');b.setAttribute('aria-label',dayLabel(p)+' '+hour(p)+' · '+number(p.temperature_2m,'°C')+' · '+number(p.precipitation,'mm'));b.append(element('span',dayLabel(p),'forecast-day'),element('span',hour(p)),element('strong',number(p.temperature_2m,'°')),element('span',number(p.precipitation,'mm'),'forecast-rain'));b.onclick=()=>select(p);strip.append(b)}
 host.append(strip,element('p','Faites défiler les heures ou touchez le graphique.','muted'));
 const NS='http://www.w3.org/2000/svg',svg=document.createElementNS(NS,'svg');svg.setAttribute('viewBox','0 0 600 280');svg.setAttribute('role','img');svg.setAttribute('aria-label','Température en courbe et pluie en barres sur 24 heures');svg.style.cssText='width:100%;display:block';
 function shape(tag,attrs,text){const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;svg.append(n);return n}
 const first=rows[0].at,last=rows[rows.length-1].at,span=Math.max(3600,last-first),x=p=>55+(p.at-first)/span*495;
 const low=temperatures.length?Math.floor(Math.min(...temperatures))-1:0,high=temperatures.length?Math.ceil(Math.max(...temperatures))+1:1;
 const y=v=>125-(v-low)/(high-low)*90;const rainMax=Math.max(1,...rows.map(p=>valid(p.precipitation)?p.precipitation:0));
 shape('text',{x:55,y:20,fill:'#326b47','font-size':14},'Température'+' · °C');
 for(const v of [low,high]){shape('line',{x1:55,x2:550,y1:y(v),y2:y(v),stroke:'#dce5dc'});shape('text',{x:48,y:y(v)+4,'text-anchor':'end','font-size':12,fill:'#58665a'},number(v,'°'))}
 let previous=null;for(const p of rows){if(valid(p.temperature_2m)){if(previous&&p.at-previous.at<=5400)shape('line',{x1:x(previous),x2:x(p),y1:y(previous.temperature_2m),y2:y(p.temperature_2m),stroke:'#326b47','stroke-width':3});shape('circle',{cx:x(p),cy:y(p.temperature_2m),r:3,fill:'#326b47'});previous=p}else previous=null}
 shape('text',{x:55,y:160,fill:'#2873a2','font-size':14},'Pluie prévue sur 1 h'+' · mm');
 shape('line',{x1:55,x2:550,y1:235,y2:235,stroke:'#dce5dc'});shape('text',{x:48,y:190,'text-anchor':'end','font-size':12,fill:'#58665a'},number(rainMax,''));shape('text',{x:48,y:239,'text-anchor':'end','font-size':12,fill:'#58665a'},'0');
 for(const p of rows){if(valid(p.precipitation)){const h=Math.max(0,p.precipitation)/rainMax*55;shape('rect',{x:x(p)-5,y:235-h,width:10,height:Math.max(1,h),rx:2,fill:'#428db6'})}else shape('text',{x:x(p),y:220,'text-anchor':'middle','font-size':12,fill:'#58665a'},'—')}
 for(const index of [...new Set([0,Math.floor((rows.length-1)/2),rows.length-1])])shape('text',{x:x(rows[index]),y:267,'text-anchor':'middle','font-size':13,fill:'#58665a'},hour(rows[index]));
 svg.onclick=e=>{const rect=svg.getBoundingClientRect(),px=(e.clientX-rect.left)/rect.width*600;select(rows.reduce((a,b)=>Math.abs(x(a)-px)<Math.abs(x(b)-px)?a:b))};
 host.append(svg,detail);select(rows[0]);
}

byId('forecast-load').onclick=async()=>{const button=byId('forecast-load');button.disabled=true;byId('forecast-state').textContent='Chargement…';try{const r=await fetch('/api/forecast',{cache:'no-store',signal:AbortSignal.timeout(20000)});if(!r.ok)throw Error();const d=await r.json();byId('forecast-state').className=d.stale?'forecast-stale':'forecast-fresh';byId('forecast-rows').replaceChildren();const rows=d.rows.filter(p=>p.at*1000>Date.now());byId('forecast-state').textContent=(d.stale?'Actualisation indisponible. Dernière copie conservée. ':'')+(d.retrieved_at?'Consultée le '+date(d.retrieved_at)+' · heure du calcul non fournie.':'Aucune prévision disponible.');
renderForecast(rows);}catch(e){byId('forecast-state').className='forecast-stale';byId('forecast-state').textContent='Actualisation impossible. Les prévisions éventuellement affichées ne sont plus actualisées.'}finally{button.disabled=false}};

byId('collect').onclick=async()=>{byId('collect').disabled=true;byId('collect-state').textContent='Envoi de la demande…';try{const response=await fetch('/api/collect',{method:'POST',headers:{'X-Botaneo-Token':'CSRF_PLACEHOLDER'}});if(!response.ok&&response.status!==409)throw Error();await refresh()}catch(e){byId('collect-state').textContent='Demande non confirmée. Actualisez la page pour vérifier son état.';byId('collect').disabled=false}};
byId('refresh').onclick=refresh;refresh();setInterval(()=>{if(!document.hidden&&!byId('sensors').contains(document.activeElement))refresh()},5000);document.addEventListener('visibilitychange',()=>{if(!document.hidden&&!byId('sensors').contains(document.activeElement))refresh()});
</script></html>'''


class Handler(BaseHTTPRequestHandler):
    def authenticated(self):
        try:
            scheme, encoded = self.headers.get('Authorization', '').split(' ', 1)
            user, auth_secret = base64.b64decode(encoded, validate=True).decode().split(':', 1)
            config = self.server.auth
            hashed = hashlib.pbkdf2_hmac('sha256', auth_secret.encode(), bytes.fromhex(config['salt']), 200000).hex()
            allowed = scheme.lower() == 'basic' and hmac.compare_digest(user, config['user']) and hmac.compare_digest(hashed, config['hash'])
        except (ValueError, UnicodeError):
            allowed = False
        if not allowed:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Gruterra", charset="UTF-8"')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return False
        return True

    def do_POST(self):
        if not self.authenticated():
            return
        if self.path == '/api/lamp':
            if not hmac.compare_digest(self.headers.get('X-Botaneo-Token',''),self.server.csrf):
                self.send_error(403); return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=2048: raise ValueError('size')
                data=json.loads(self.rfile.read(size))
                with sqlite3.connect((BASE/'data/collector.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
                    if not db.execute('SELECT 1 FROM sensor_status WHERE sensor_id=?',(data['sensor'],)).fetchone():raise ValueError('sensor')
                with self.server.request_lock:
                    save_lamp(BASE/'config/light-schedules.json',data['sensor'],data['start'],data['end'])
            except (ValueError,KeyError,TypeError,sqlite3.Error,OSError):
                self.send_error(400);return
            self.send_response(204);self.send_header('Content-Length','0');self.end_headers();return
        if self.path != '/api/collect' or not hmac.compare_digest(self.headers.get('X-Botaneo-Token', ''), self.server.csrf):
            self.send_error(403)
            return
        with self.server.request_lock:
            state = collection_state()
            if state.get('running') or state.get('pending'):
                self.send_error(409, 'Collection already running')
                return
            try:
                with (BASE/'data/collect.request').open('x') as stream:
                    stream.write('manual')
            except FileExistsError:
                self.send_error(409)
                return
        self.send_response(202)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        if not self.authenticated():
            return
        lang=language(self.path,self.headers.get('Cookie',''))
        route=urlsplit(self.path).path
        if route == '/':
            body, kind, status = render(HTML,lang).replace('CSRF_PLACEHOLDER', self.server.csrf).encode(), 'text/html; charset=utf-8', 200
        elif route == '/weather':
            body, kind, status = render(WEATHER_HTML,lang).encode(), 'text/html; charset=utf-8', 200
        elif route == '/api/weather':
            try:
                body = json.dumps(weather_snapshot(BASE/'data/weather.sqlite3')).encode()
                kind, status = 'application/json', 200
            except (sqlite3.Error, OSError, ValueError, KeyError, TypeError):
                body, kind, status = b'{"error":"unavailable"}', 'application/json', 503
        elif route == '/api/forecast':
            body, kind, status = json.dumps(forecast()).encode(), 'application/json', 200
        elif route == '/api/status':
            try:
                data = snapshot(BASE/'data/collector.sqlite3')
                data['collection'] = collection_state()
                if lang=='en':
                    message=data['collection'].get('message','')
                    data['collection']['message']=EN.get(message,'Collector status available in sensor details.')
                body = json.dumps(data).encode()
                kind, status = 'application/json', 200
            except (sqlite3.Error, OSError):
                body, kind, status = b'{"error":"unavailable"}', 'application/json', 503
        else:
            body, kind, status = b'Not found', 'text/plain', 404
        self.send_response(status)
        if route in ('/','/weather'):
            self.send_header('Set-Cookie','gruterra_lang='+lang+'; Path=/; Max-Age=31536000; SameSite=Lax; HttpOnly')
            self.send_header('Content-Language',lang)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def collection_state():
    try:
        state = json.loads((BASE/'data/collect-state.json').read_text())
    except (OSError, ValueError):
        state = {'running': False, 'message': 'Collecteur en attente.'}
    state['pending'] = (BASE/'data/collect.request').exists()
    return state


if __name__ == '__main__':
    auth = json.loads((BASE/'config/web-auth.json').read_text())
    if not auth.get('user') or len(bytes.fromhex(auth['salt'])) != 16 or len(bytes.fromhex(auth['hash'])) != 32:
        raise ValueError('Invalid authentication configuration')
    server = ThreadingHTTPServer(('0.0.0.0', 8765), Handler)
    server.auth = auth
    server.csrf = secrets.token_urlsafe(32)
    server.request_lock = threading.Lock()
    server.serve_forever()

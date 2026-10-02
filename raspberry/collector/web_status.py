"""Authenticated mobile dashboard with queued collection requests."""
import json
import base64
import hashlib
import hmac
import secrets
import threading
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path.home() / 'botaneo'


def snapshot(path):
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        sensors = []
        for status in db.execute('SELECT * FROM sensor_status ORDER BY sensor_id'):
            row = db.execute('SELECT * FROM measurements WHERE sensor_id=? ORDER BY rowid DESC LIMIT 1',
                             (status['sensor_id'],)).fetchone()
            sensors.append({'status': dict(status), 'latest': dict(row) if row else None})
        pending = sum(db.execute(f"SELECT COUNT(*) FROM {table} WHERE sync_state='pending'").fetchone()[0]
                      for table in ('measurements', 'history_measurements'))
        history = db.execute('SELECT COUNT(*) FROM history_measurements').fetchone()[0]
        return {'sensors': sensors, 'pending': pending, 'history': history,
                'checked_at': datetime.now(timezone.utc).isoformat()}
    finally:
        db.close()


HTML = '''<!doctype html><html lang="fr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Botanéo · Raspberry</title><style>
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
</style><main><h1>Botanéo</h1>
<p class="muted">Votre collecteur Raspberry</p><p id="connection" role="status">Chargement…</p>
<button id="collect">Lire les capteurs maintenant</button><p id="collect-state" aria-live="polite"></p><div id="sensors"></div><section class="card"><h2>Synchronisation PC</h2><p id="pending">—</p>
<p class="muted">Les relevés restent conservés sur le Raspberry. Le PC les récupère lorsque Botanéo est ouvert et que les deux appareils peuvent communiquer.</p></section>
<button id="refresh">Actualiser l’affichage</button><p class="muted">Actualiser affiche les données déjà enregistrées. « Lire les capteurs » demande une nouvelle lecture, qui peut prendre plusieurs minutes. Actualisation automatique tant que cette page est visible.</p></main>
<script>
const byId=id=>document.getElementById(id);
function element(tag,text,cls){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e}
function date(value){return value?new Date(value).toLocaleString('fr-FR'):'Aucune'}
function age(value){const n=Date.now()-new Date(value).getTime();if(!value||!Number.isFinite(n)||n<0)return 'Date à vérifier';const m=Math.floor(n/60000);return m<1?'À l’instant':m<60?'Il y a '+m+' min':m<1440?'Il y a '+Math.floor(m/60)+' h':'Il y a '+Math.floor(m/1440)+' j'}
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
c.append(element('h2','Capteur '+(data.sensors.indexOf(sensor)+1)));const old=!m||m.time_quality!=='ntp'||Date.now()-new Date(m.measured_at).getTime()>12*3600000;c.append(element('p',m?age(m.measured_at):'En attente de première mesure','badge'+(old?' warning':'')));
if(m){const grid=element('div','','grid');
for(const [label,value,unit] of [['Température',m.temperature_c,'°C'],['Humidité du sol',m.moisture_percent,'%'],['Lumière',m.illuminance_lux,'lux'],['Conductivité',m.conductivity_us_cm,'µS/cm']]){
const cell=element('div','');cell.append(element('div',label,'muted'),element('div',(typeof value==='number'?value.toLocaleString('fr-FR',{maximumFractionDigits:1}):'—')+' '+unit,'value'));grid.append(cell)}c.append(grid);
c.append(element('p','Dernier relevé : '+date(m.measured_at),'muted'));
if(m.time_quality!=='ntp')c.append(element('p','Date non confirmée : horloge du Raspberry à vérifier.','warning'));
else if(Date.now()-new Date(m.measured_at).getTime()>12*3600000)c.append(element('p','Relevé ancien : plus de 12 heures.','warning'));
}else c.append(element('p','Aucune mesure disponible.'));
if(s.last_error)c.append(element('p','Dernière collecte en échec. Les dernières valeurs sont conservées.','warning'));
const details=element('details','');details.dataset.sensor=s.sensor_id;details.open=expanded.has(s.sensor_id);details.append(element('summary','Détails du capteur'),element('p',s.sensor_id),element('p','Dernière tentative : '+date(s.last_attempt)),element('p','Dernière réussite : '+date(s.last_success)));c.append(details);byId('sensors').append(c)}
if(!data.sensors.length)byId('sensors').append(element('p','Aucun capteur enregistré.'));
byId('pending').textContent=data.pending+' relevé(s) en attente de confirmation du PC · '+data.history+' relevé(s) historiques conservés.';
}catch(e){byId('connection').className='offline';byId('connection').textContent='Connexion interrompue · les valeurs affichées ne sont plus actualisées.';byId('collect').disabled=true}finally{refreshing=false}}
byId('collect').onclick=async()=>{byId('collect').disabled=true;byId('collect-state').textContent='Envoi de la demande…';try{const response=await fetch('/api/collect',{method:'POST',headers:{'X-Botaneo-Token':'CSRF_PLACEHOLDER'}});if(!response.ok&&response.status!==409)throw Error();await refresh()}catch(e){byId('collect-state').textContent='Demande non confirmée. Actualisez la page pour vérifier son état.';byId('collect').disabled=false}};
byId('refresh').onclick=refresh;refresh();setInterval(()=>{if(!document.hidden)refresh()},5000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
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
            self.send_header('WWW-Authenticate', 'Basic realm="Botaneo", charset="UTF-8"')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return False
        return True

    def do_POST(self):
        if not self.authenticated():
            return
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
        if self.path == '/':
            body, kind, status = HTML.replace('CSRF_PLACEHOLDER', self.server.csrf).encode(), 'text/html; charset=utf-8', 200
        elif self.path == '/api/status':
            try:
                data = snapshot(BASE/'data/collector.sqlite3')
                data['collection'] = collection_state()
                body = json.dumps(data).encode()
                kind, status = 'application/json', 200
            except (sqlite3.Error, OSError):
                body, kind, status = b'{"error":"unavailable"}', 'application/json', 503
        else:
            body, kind, status = b'Not found', 'text/plain', 404
        self.send_response(status)
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

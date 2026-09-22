"""Local read-only dashboard; no Bluetooth commands or database mutations."""
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
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Botanéo · Raspberry</title><style>
body{font:17px system-ui;margin:0;background:#f2f6f1;color:#223228}main{max-width:650px;margin:auto;padding:24px 18px}
h1{margin-bottom:4px}p{line-height:1.5}.card{background:white;padding:20px;border-radius:18px;margin:16px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.value{font-size:27px;font-weight:650}
.muted{color:#58665a;font-size:14px}button{background:#326b47;color:white;border:0;border-radius:12px;padding:14px;font:inherit;width:100%}
.warning{color:#93421c}h2{font-size:20px}</style><main><h1>Botanéo</h1>
<p class="muted">Votre collecteur Raspberry</p><p id="connection">Chargement…</p>
<button id="collect">Lire les capteurs maintenant</button><p id="collect-state" aria-live="polite"></p><div id="sensors"></div><section class="card"><h2>Synchronisation PC</h2><p id="pending">—</p>
<p class="muted">Les relevés restent conservés sur le Raspberry. Le PC les récupère lorsque Botanéo est ouvert et que les deux appareils peuvent communiquer.</p></section>
<button id="refresh">Actualiser l’affichage</button><p class="muted">Cette page consulte les données enregistrées. Elle ne déclenche aucune lecture Bluetooth. Actualisation automatique toutes les 5 secondes. La lecture des capteurs peut prendre plusieurs minutes.</p></main>
<script>
const byId=id=>document.getElementById(id);
function element(tag,text,cls){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e}
function date(value){return value?new Date(value).toLocaleString('fr-FR'):'Aucune'}
async function refresh(){try{
const r=await fetch('/api/status',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();
byId('connection').textContent='Raspberry joignable · '+date(data.checked_at);
byId('collect').disabled=Boolean(data.collection.running||data.collection.pending);
byId('collect-state').textContent=data.collection.pending?'Demande enregistrée…':data.collection.message;
byId('sensors').replaceChildren();
for(const sensor of data.sensors){const s=sensor.status,m=sensor.latest,c=element('section','','card');
c.append(element('h2','Capteur '+s.sensor_id));
if(m){const grid=element('div','','grid');
for(const [label,value,unit] of [['Température',m.temperature_c,'°C'],['Humidité du sol',m.moisture_percent,'%'],['Lumière',m.illuminance_lux,'lux'],['Conductivité',m.conductivity_us_cm,'µS/cm']]){
const cell=element('div','');cell.append(element('div',label,'muted'),element('div',value+' '+unit,'value'));grid.append(cell)}c.append(grid);
c.append(element('p','Dernier relevé : '+date(m.measured_at),'muted'));
if(m.time_quality!=='ntp')c.append(element('p','Date non confirmée : horloge du Raspberry à vérifier.','warning'));
else if(Date.now()-new Date(m.measured_at).getTime()>12*3600000)c.append(element('p','Relevé ancien : plus de 12 heures.','warning'));
}else c.append(element('p','Aucune mesure disponible.'));
if(s.last_error)c.append(element('p','Dernière collecte en échec. Les dernières valeurs sont conservées.','warning'));
c.append(element('p','Dernière tentative : '+date(s.last_attempt),'muted'));byId('sensors').append(c)}
if(!data.sensors.length)byId('sensors').append(element('p','Aucun capteur enregistré.'));
byId('pending').textContent=data.pending+' relevé(s) en attente de confirmation du PC · '+data.history+' relevé(s) historiques conservés.';
}catch(e){byId('connection').textContent='Raspberry indisponible. Les valeurs affichées peuvent être anciennes.'}}
byId('collect').onclick=async()=>{byId('collect').disabled=true;byId('collect-state').textContent='Envoi de la demande…';try{const response=await fetch('/api/collect',{method:'POST',headers:{'X-Botaneo-Token':'CSRF_PLACEHOLDER'}});if(!response.ok&&response.status!==409)throw Error();await refresh()}catch(e){byId('collect-state').textContent='Demande non confirmée. Actualisez la page pour vérifier son état.';byId('collect').disabled=false}};
byId('refresh').onclick=refresh;refresh();setInterval(refresh,5000);
</script></html>'''


class Handler(BaseHTTPRequestHandler):
    def authenticated(self):
        try:
            scheme, encoded = self.headers.get('Authorization', '').split(' ', 1)
            user, password = base64.b64decode(encoded, validate=True).decode().split(':', 1)
            config = self.server.auth
            hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(config['salt']), 200000).hex()
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

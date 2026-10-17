"""Essai isolé des modules applicatifs. Simulation par défaut, réseau explicite."""
import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

ORIGIN='https://api.gruterra.fr'
PATHS={'/v2/challenges','/v2/contributions','/v2/withdrawals'}
LIMIT=1048576


ALLOWED_ERRORS=frozenset({
    'challenge_limit','challenge_unavailable','contribution_expired','contribution_withdrawn',
    'contribution_unavailable','https_required','identity_conflict','invalid_request',
    'invalid_signature','json_required','maintenance','method_not_allowed','not_found',
    'payload_too_large','request_id_conflict','service_not_configured',
    'signatures_unavailable','storage_unavailable','unauthorized','v2_disabled'})


class SafeTransportError(ValueError):
    def __init__(self,status=None):
        super().__init__('Transport failed')
        self.status=status if type(status) is int and 100<=status<=599 else None


class Diagnostic:
    def __init__(self):
        self.stage='Initialisation';self.status=None;self.error=None;self.reported=False

    def enter(self,stage):
        self.stage=stage;self.status=None;self.error=None
        print('ÉTAPE : '+stage,flush=True)

    def response(self,status,body):
        self.status=status if type(status) is int and 100<=status<=599 else None
        value=body.get('error') if type(body) is dict else None
        self.error=value if type(value) is str and value in ALLOWED_ERRORS else ('non reconnu' if value is not None else None)
        print('HTTP : '+str(self.status or 'indisponible')+(' · code serveur : '+self.error if self.error else ''),flush=True)

    def failed(self,exception):
        self.reported=True
        if isinstance(exception,SafeTransportError):self.status=exception.status
        print('ÉCHEC · étape : '+self.stage+' · HTTP : '+str(self.status or 'indisponible')+
              ' · code serveur : '+(self.error or 'non disponible'),flush=True)



def decode_response(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate response field')
            result[key]=value
        return result
    if len(raw)>LIMIT:raise ValueError('Response too large')
    result=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    if type(result) is not dict:raise ValueError('Invalid response')
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        code=args[2] if len(args)>2 else kwargs.get('code')
        raise SafeTransportError(code)


class PrivateTransport:
    def __init__(self,token):
        if not token or any(c in token for c in '\r\n'):raise ValueError('Invalid token')
        self._token=token
        self._opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))

    def __call__(self,path,body):
        if path not in PATHS:raise ValueError('Endpoint refused')
        request=urllib.request.Request(ORIGIN+path,data=json.dumps(body,ensure_ascii=False).encode('utf-8'),method='POST',
            headers={'Content-Type':'application/json','Authorization':'Bearer '+self._token})
        try:
            response=self._opener.open(request,timeout=20)
        except urllib.error.HTTPError as error:
            response=error
        except (urllib.error.URLError,TimeoutError,OSError):
            raise SafeTransportError() from None
        with response:
            status=response.code
            try:
                if response.geturl()!=ORIGIN+path:raise ValueError('Endpoint changed')
                raw=response.read(LIMIT+1)
                return status,decode_response(raw)
            except (ValueError,UnicodeError,OSError):
                raise SafeTransportError(status) from None


@contextmanager
def isolated_modules():
    # Must be a fresh process: environment override precedes imports.
    if any(name in sys.modules for name in ('botaneo_config','contribution_identite','contribution_suivi','contribution_protocole')):
        raise RuntimeError('Run in a separate process')
    previous={key:os.environ.get(key) for key in ('BOTANEO_CONFIG_DIR','BOTANEO_DEMO')}
    with tempfile.TemporaryDirectory(prefix='gruterra-api-private-') as folder:
        os.environ['BOTANEO_CONFIG_DIR']=folder
        os.environ['BOTANEO_DEMO']='0'
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
        try:
            import botaneo_config as config
            import contribution_identite as identity
            import contribution_protocole as protocol
            import contribution_suivi as tracking
            expected=Path(folder).resolve()
            if any(m.CONFIG_DIR.resolve()!=expected for m in (config,identity,tracking)):
                raise RuntimeError('Isolation failed')
            yield identity,protocol,tracking
        finally:
            for key,value in previous.items():
                if value is None:os.environ.pop(key,None)
                else:os.environ[key]=value


class SimulatedAPI:
    """Only fictitious data; verify signatures instead of bypassing them."""
    def __init__(self):
        self.now=datetime.now(timezone.utc).replace(microsecond=0)
        self.challenges={};self.receipts={};self.withdrawn=set()

    def wait(self,seconds):self.now+=timedelta(seconds=seconds)

    def __call__(self,path,body):
        if path=='/v2/challenges':
            challenge={'protocol_version':2,'challenge_id':str(uuid.uuid4()),'nonce':base64.b64encode(os.urandom(32)).decode(),'expires_at':(self.now+timedelta(seconds=300)).strftime('%Y-%m-%dT%H:%M:%SZ')}
            self.challenges[challenge['challenge_id']]=(challenge,body)
            return 201,challenge
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        import contribution_protocole as protocol
        challenge,owner=self.challenges.pop(body['challenge_id'])
        operation='contribute' if path=='/v2/contributions' else 'withdraw'
        assert owner['operation']==operation and owner['contributor_id']==body['contributor_id']
        payload=base64.b64decode(body['payload_b64'],validate=True)
        public={k:body[k] for k in ('contributor_id','public_key')}
        message=protocol.message_signe(operation,public,body['request_id'],body['challenge_id'],challenge['nonce'],payload)
        Ed25519PublicKey.from_public_bytes(base64.b64decode(body['public_key'])).verify(base64.b64decode(body['signature']),message)
        request=body['request_id']
        if operation=='contribute' and request in self.withdrawn:return 410,{'error':'contribution_withdrawn'}
        if request in self.receipts:
            prior=self.receipts[request]
            if operation=='contribute' and self.now>=datetime.fromisoformat(prior['retention_until'].replace('Z','+00:00')):
                return 410,{'error':'contribution_expired'}
            return 200,prior
        receipt={'protocol_version':2,'mode':'private_test','contributor_id':body['contributor_id'],'request_id':request}
        if operation=='contribute':
            receipt.update(status='accepted',contribution_id=str(uuid.uuid4()),schema_version=2,payload_sha256=hashlib.sha256(payload).hexdigest(),received_at=self.now.strftime('%Y-%m-%dT%H:%M:%SZ'),retention_until=(self.now+timedelta(seconds=60)).strftime('%Y-%m-%dT%H:%M:%SZ'),withdrawal_endpoint=ORIGIN+'/v2/withdrawals',policy_version='lifecycle-test-60s')
        else:
            data=json.loads(payload);count=0
            for key,prior in self.receipts.items():
                if prior['status']=='accepted' and (data['scope']=='all' or prior['contribution_id']==data['contribution_id']):
                    if key not in self.withdrawn:count+=1
                    self.withdrawn.add(key)
            receipt.update(status='withdrawn',scope=data['scope'],withdrawn_count=count,processed_at=self.now.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.receipts[request]=receipt
        return 201,receipt


def run(post,wait,now,diagnostic=None):
    diagnostic=diagnostic or Diagnostic()
    diagnostic.enter('Isolation des fichiers privés')
    with isolated_modules() as (identity,protocol,tracking):
        diagnostic.enter('Création de l’identité fictive')
        identity.preparer_identite();public=identity.identite_publique()
        payload=(Path(__file__).resolve().parents[1]/'tests/fixtures/contribution_donnees_v2.json').read_bytes()
        prepared=[]
        def prepare(operation,content):
            diagnostic.enter('Préparation locale de la demande')
            request=tracking.preparer_demande(public['contributor_id'],operation,content,profil_test='lifecycle-test-60s')
            prepared.append(request);tracking.marquer_en_attente(request)
            return request
        phase='Parcours'
        def send(request):
            row=tracking.lire_demande(request)
            diagnostic.enter(phase+' · obtention du défi')
            code,challenge=post('/v2/challenges',{'protocol_version':2,**public,'operation':row['operation']})
            diagnostic.response(code,challenge)
            if code!=201:raise ValueError('Challenge refused')
            diagnostic.enter(phase+' · validation du défi et signature locale')
            envelope=protocol.enveloppe_signee(row['operation'],row['payload'],request,challenge,now=now())
            diagnostic.enter(phase+' · réponse de l’opération signée')
            code,result=post(protocol.PATHS[row['operation']],envelope)
            diagnostic.response(code,result)
            # Keep the HTTP result when local validation rejects the receipt.
            if code in (200,201,410):diagnostic.stage=phase+' · validation applicative de la réponse'
            if code in (200,201):tracking.enregistrer_recu(request,result,code)
            elif code==410:tracking.enregistrer_fin_parcours(request,result,code)
            else:raise ValueError('Unexpected HTTP status')
            return code,result
        checks=[];cleanup=False
        def success(text):
            checks.append(text);print('OK : '+text,flush=True)
        try:
            phase='Première contribution'
            first=prepare('contribute',payload)
            code,receipt=send(first)
            if code!=201:raise ValueError('First receipt expected')
            success('Réception 201 validée par les modules applicatifs')
            phase='Reprise de la première contribution'
            code,replay=send(first)
            if code!=200 or replay!=receipt:raise ValueError('Receipt changed')
            success('Reprise 200 : mêmes octets, référence et échéance')
            diagnostic.enter('Vérification de l’horloge et attente de l’échéance')
            expiry=datetime.fromisoformat(receipt['retention_until'].replace('Z','+00:00'))
            delay=(expiry-now()).total_seconds()+2
            if not 0<delay<=65:raise ValueError('Clock incompatible with test')
            wait(delay)
            local=tracking.etat_local(first,now())
            if local['status']!='deadline_reached' or local['server_deletion_verified']:raise ValueError('Local state invalid')
            success('Échéance locale distincte de la suppression serveur')
            phase='Reprise après échéance'
            code,result=send(first)
            if code!=410 or result!={'error':'contribution_expired'}:raise ValueError('Expiry not confirmed')
            success('Expiration 410, reçu initial préservé')
            phase='Seconde contribution'
            second=prepare('contribute',payload);code,accepted=send(second)
            if code!=201:raise ValueError('Second receipt expected')
            phase='Retrait ciblé'
            removal=prepare('withdraw',json.dumps({'scope':'contribution','contribution_id':accepted['contribution_id']}).encode())
            if send(removal)[0]!=201:raise ValueError('Withdrawal not confirmed')
            phase='Reprise après retrait'
            code,result=send(second)
            if code!=410 or result!={'error':'contribution_withdrawn'}:raise ValueError('Withdrawal replay not refused')
            success('Retrait signé et refus de recréation')
        except Exception as failure:
            diagnostic.failed(failure)
            raise
        finally:
            phase='Nettoyage'
            diagnostic.enter('Nettoyage de l’identité fictive')
            # Uncertain requests must be retried before another operation, to
            # retain serialization rather than bypass local safety checks.
            try:
                for request in prepared:
                    if tracking.lire_demande(request)['state'] in ('pending','check'):send(request)
                removal=prepare('withdraw',b'{"scope":"all"}')
                cleanup=send(removal)[0] in (200,201)
            except Exception as failure:
                diagnostic.failed(failure)
                print('NETTOYAGE NON CONFIRMÉ : intervention côté API nécessaire pour l’identité fictive '+public['contributor_id'])
            if cleanup:print('Nettoyage fictif confirmé ; traces techniques conservées côté serveur.')
        if not cleanup:raise RuntimeError('Cleanup not confirmed')
        return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network',action='store_true',help='Essai privé HTTPS explicite ; API à ouvrir temporairement côté serveur')
    args=parser.parse_args()
    diagnostic=Diagnostic()
    try:
        if args.network:
            from getpass import getpass
            diagnostic.enter('Saisie masquée du jeton et préparation HTTPS')
            post=PrivateTransport(getpass('Jeton privé de test (non enregistré) : '))
            wait=time.sleep;now=lambda:datetime.now(timezone.utc)
            print('ESSAI PRIVÉ RÉSEAU : identité temporaire, données fictives uniquement.')
        else:
            post=SimulatedAPI();wait=post.wait;now=lambda:post.now
            print('SIMULATION LOCALE : aucun appel réseau.')
        run(post,wait,now,diagnostic)
        print('Le serveur doit être refermé après un essai réseau. Ce lanceur ne modifie pas sa configuration.')
        return 0
    except Exception as failure:
        if not diagnostic.reported:diagnostic.failed(failure)
        # Do not print arbitrary transport errors which could contain secrets.
        print('ÉCHEC de l’essai privé. Aucun succès global affirmé ; vérifier le nettoyage et la fermeture côté serveur.')
        return 1


if __name__=='__main__':raise SystemExit(main())

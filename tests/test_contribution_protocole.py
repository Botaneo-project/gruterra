import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import contribution_identite as identity
import contribution_protocole as protocol
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.vector = json.loads((Path(__file__).parent/'fixtures/contribution_signature_v2.json').read_text(encoding='utf-8'))
        self.public = {key:self.vector[key] for key in ('contributor_id','public_key')}
        self.payload = base64.b64decode(self.vector['payload_b64'])

    def build(self, **changes):
        args = dict(operation='contribute', public=self.public, request_id=self.vector['request_id'],
                    challenge_id=self.vector['challenge_id'], nonce=self.vector['nonce'], payload=self.payload)
        args.update(changes)
        return protocol.message_signe(**args)

    def test_same_exact_message_as_php_public_vector(self):
        message=self.build()
        self.assertEqual(base64.b64decode(self.vector['signed_message_b64']), message)
        self.assertFalse(message.endswith(b'\n'))
        self.assertNotIn(b'\r',message)
        self.assertEqual(hashlib.sha256(self.payload).hexdigest(),self.vector['payload_sha256'])
        key=Ed25519PublicKey.from_public_bytes(base64.b64decode(self.vector['public_key']))
        key.verify(base64.b64decode(self.vector['signature']),message)

    def test_changes_to_signed_components_rejected_by_signature(self):
        key=Ed25519PublicKey.from_public_bytes(base64.b64decode(self.vector['public_key']))
        signature=base64.b64decode(self.vector['signature'])
        for message in (self.build()+b'\n', self.build(operation='withdraw'),
                        self.build(payload=self.payload+b' '),
                        self.build(challenge_id='30000000-0000-4000-8000-000000000003')):
            with self.assertRaises(InvalidSignature):key.verify(signature,message)

    def test_bad_identifiers_and_noncanonical_base64_rejected(self):
        for changes in ({'operation':'unknown'}, {'request_id':'id\ninjected'},
                        {'nonce':self.vector['nonce'].rstrip('=')},
                        {'public':dict(self.public,contributor_id='ed25519:wrong')},
                        {'payload':self.payload.decode('utf-8')}):
            with self.assertRaises(ValueError):self.build(**changes)

    def test_retries_use_same_bytes_and_id_with_new_challenge(self):
        now=datetime(2026,10,10,12,0,tzinfo=timezone.utc)
        challenge={'protocol_version':2,'challenge_id':self.vector['challenge_id'],
                   'nonce':self.vector['nonce'],'expires_at':'2026-10-10T12:05:00Z'}
        with tempfile.TemporaryDirectory() as folder, patch.object(identity,'CONFIG_DIR',Path(folder)), patch.dict(os.environ,{'BOTANEO_DEMO':'0'}):
            identity.preparer_identite()
            first=protocol.enveloppe_signee('contribute',self.payload,self.vector['request_id'],challenge,now=now)
            fresh=dict(challenge,challenge_id='30000000-0000-4000-8000-000000000003')
            retry=protocol.enveloppe_signee('contribute',self.payload,self.vector['request_id'],fresh,now=now)
            self.assertEqual(first['request_id'],retry['request_id'])
            self.assertEqual(first['payload_b64'],retry['payload_b64'])
            self.assertNotEqual(first['signature'],retry['signature'])
            self.assertEqual(set(first),{'protocol_version','contributor_id','public_key','request_id','challenge_id','payload_b64','signature'})
            key=Ed25519PublicKey.from_public_bytes(base64.b64decode(first['public_key']))
            public={k:first[k] for k in ('contributor_id','public_key')}
            message=protocol.message_signe('contribute',public,first['request_id'],first['challenge_id'],challenge['nonce'],self.payload)
            key.verify(base64.b64decode(first['signature']),message)
            with patch.dict(os.environ,{'BOTANEO_DEMO':'1'}):
                with self.assertRaises(ValueError):
                    protocol.enveloppe_signee('contribute',self.payload,self.vector['request_id'],challenge,now=now)

    def test_expired_or_malformed_challenge_rejected(self):
        now=datetime(2026,10,10,12,0,tzinfo=timezone.utc)
        challenge={'protocol_version':2,'challenge_id':self.vector['challenge_id'],
                   'nonce':self.vector['nonce'],'expires_at':'2026-10-10T12:00:00Z'}
        with self.assertRaises(ValueError):protocol.verifier_defi(challenge,now)
        for changes in ({'expires_at':'2026-10-10T12:05:00'}, {'protocol_version':True}, {'nonce':'bad'}):
            with self.assertRaises(ValueError):protocol.verifier_defi(dict(challenge,**changes),now)

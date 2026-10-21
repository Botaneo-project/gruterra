"""Read-only local conversion audit markers, never rescale archived values."""
from datetime import datetime
import json,os
from pathlib import Path


def load_notes(path=None):
    if os.environ.get('BOTANEO_DEMO')=='1':return []
    if path is None:
        from botaneo_config import CONFIG_DIR
        path=CONFIG_DIR/'zigbee_decoder_transition.local.json'
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        instant=datetime.fromisoformat(data['activated_at'])
        if data.get('schema_version')!=1 or instant.tzinfo is None:return []
        devices=data['hardware_ids']
        if not isinstance(devices,list) or not all(isinstance(d,str) for d in devices):return []
        return [{'at':instant.timestamp(),'hardware_ids':devices,'date':instant.isoformat()}]
    except (OSError,ValueError,KeyError,TypeError):return []


def relevant_notes(notes,rows,metric='illuminance'):
    if metric!='illuminance':return []
    devices={r['hardware_id'] for r in rows if r.get('metric')==metric}
    return [n for n in notes if devices.intersection(n['hardware_ids'])]

"""Explicitly confirmed, bounded HA catch-up. No scheduler or plant imports."""
from datetime import datetime, timedelta
import os
from home_assistant_archive import checkpoint, commit_history, digest, scope
from home_assistant_client import validate_config
from home_assistant_history import read_history
from home_assistant_registry import authorized_selection
from home_assistant_sensors import utc


def plan_catchup(config, archive_path, *, start, end, received_at, plant_db_path=None, max_windows=4):
    if os.environ.get('BOTANEO_DEMO') == '1':
        raise ValueError('demo_disabled')
    active = {**config, 'enabled': True}
    validate_config(active)
    authorized_selection(active['entities'], db_path=plant_db_path)
    if type(max_windows) is not int or not 1 <= max_windows <= 4:
        raise ValueError('invalid_window_limit')
    begin = datetime.fromisoformat(utc(start))
    finish = datetime.fromisoformat(utc(end))
    now = datetime.fromisoformat(utc(received_at))
    if not begin < finish <= now or (finish-begin).total_seconds() > 7*86400:
        raise ValueError('invalid_catchup_range')
    saved = checkpoint(archive_path, active, plant_db_path=plant_db_path)
    current = datetime.fromisoformat(saved) if saved else begin
    if current < begin:
        raise ValueError('requested_range_skips_checkpoint')
    windows = []
    while current < finish and len(windows) < max_windows:
        stop = min(current+timedelta(hours=6), finish)
        windows.append({'start': current.isoformat(), 'end': stop.isoformat()})
        current = stop
    plan = {'schema_version': 1, 'scope': scope(active), 'requested_start': utc(start),
            'target_end': utc(end), 'windows': windows, 'max_windows': max_windows,
            'initial_checkpoint': saved, 'more_pending': current < finish,
            'destination': 'separate_ha_archive', 'plant_import': False,
            'retention_verified': False}
    return {**plan, 'plan_id': digest(plan)}


def run_catchup(config, plan, archive_path, *, confirmed=False, received_at, plant_db_path=None, requester=None):
    if confirmed is not True:
        return {'ok': False, 'code': 'confirmation_required', 'completed_windows': 0}
    completed = 0
    totals = {'facts_added': 0, 'revisions_added': 0, 'duplicates': 0}
    try:
        fresh = plan_catchup(config, archive_path, start=plan['requested_start'], end=plan['target_end'],
                             received_at=received_at, plant_db_path=plant_db_path, max_windows=plan['max_windows'])
        if fresh != plan:
            raise ValueError('plan_changed')
        active = {**config, 'enabled': True}
        # Dense histories are split without advancing the cursor on a failed read.
        # A fixed request budget keeps one application sync bounded.
        pending = list(plan['windows'])
        requests_left = 16
        while pending and requests_left:
            window = pending.pop(0)
            owners, ble = authorized_selection(active['entities'], db_path=plant_db_path)
            requests_left -= 1
            batch = read_history(active, owners=owners, existing_ble_addresses=ble,
                                 start=window['start'], end=window['end'], received_at=received_at, requester=requester)
            if not batch.get('ok'):
                begin = datetime.fromisoformat(window['start'])
                end = datetime.fromisoformat(window['end'])
                if batch.get('code') == 'history_too_large' and (end-begin).total_seconds() > 60:
                    middle = begin + (end-begin)/2
                    pending[0:0] = [dict(start=begin.isoformat(), end=middle.isoformat()),
                                    dict(start=middle.isoformat(), end=end.isoformat())]
                    continue
                return {'ok': False, 'code': 'history_read_failed', 'http_status': batch.get('http_status'),
                        'reason': batch.get('code') if batch.get('code') in ('history_too_large', 'history_connection_failed', 'history_http_error') else 'invalid_history',
                        'completed_windows': completed, **totals}
            result = commit_history(archive_path, active, batch, plant_db_path=plant_db_path)
            completed += 1
            for key in totals:
                totals[key] += result[key]
        more = bool(pending) or plan['more_pending']
        # Without a single successful chunk, repeating the same plan cannot progress.
        if pending and not completed:
            return {'ok': False, 'code': 'history_read_failed', 'completed_windows': 0, **totals}
        return {'ok': True, 'code': 'more_pending' if more else 'complete',
                'completed_windows': completed, **totals, 'plant_import': False,
                'retention_verified': False, 'checkpoint': checkpoint(archive_path, active, plant_db_path=plant_db_path)}
    except ValueError as error:
        allowed = {'demo_disabled', 'mapping_not_authorized', 'plan_changed', 'invalid_catchup_range', 'requested_range_skips_checkpoint', 'plant_database_forbidden'}
        return {'ok': False, 'code': str(error) if str(error) in allowed else 'catchup_invalid',
                'completed_windows': completed, **totals}
    except Exception:
        return {'ok': False, 'code': 'catchup_interrupted', 'completed_windows': completed, **totals}

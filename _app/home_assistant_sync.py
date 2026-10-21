"""Bounded Home Assistant catch-up as part of an explicitly enabled app sync."""
import os
from datetime import datetime,timedelta,timezone
from pathlib import Path
from threading import Lock
_LOCK=Lock()


def synchronize(*,config=None,archive_path=None,now=None,plant_db_path=None,requester=None):
    if os.environ.get('BOTANEO_DEMO')=='1':
        return {'status':'demo_disabled'}
    from home_assistant_ui import load
    from home_assistant_archive import checkpoint
    from home_assistant_sensors import utc
    from home_assistant_catchup import plan_catchup,run_catchup
    from botaneo_config import DATA_DIR
    try:
        cfg=config if config is not None else load()
        if cfg.get('sync_on_request') is not True:
            return {'status':'disabled'}
        if not _LOCK.acquire(blocking=False):
            return {'status':'busy'}
        try:
            archive=Path(archive_path) if archive_path is not None else Path(DATA_DIR)/'home_assistant_history.sqlite3'
            instant=datetime.fromisoformat(utc(now)) if now else datetime.now(timezone.utc)
            saved=checkpoint(archive,cfg,plant_db_path=plant_db_path)
            start=datetime.fromisoformat(saved) if saved else instant-timedelta(days=1)
            if start >= instant:
                return {'status':'complete','facts_added':0,'duplicates':0,'plant_import':False}
            # Keep the stored cursor, even after a long absence; never skip old windows.
            target=min(instant,start+timedelta(days=7))
            plan=plan_catchup(cfg,archive,start=start.isoformat(),end=target.isoformat(),received_at=instant.isoformat(),plant_db_path=plant_db_path)
            archive.parent.mkdir(parents=True,exist_ok=True)
            result=run_catchup(cfg,plan,archive,confirmed=True,received_at=instant.isoformat(),plant_db_path=plant_db_path,requester=requester)
            if result.get('ok') and target < instant:
                result={**result,'code':'more_pending'}
            return {**result,'status':('more_pending' if result.get('code')=='more_pending' else 'complete') if result.get('ok') else 'failed'}
        finally:
            _LOCK.release()
    except Exception:
        return {'status':'failed'}


def result_message(result):
    from i18n import traduire_courant as t
    status=result.get('status','failed')
    if status in ('disabled','demo_disabled'):return ''
    if status in ('complete','more_pending'):
        return t('ha_sync_done').format(count=result.get('facts_added',0),duplicates=result.get('duplicates',0))+(' '+t('ha_catchup_more') if status=='more_pending' else '')
    if status=='busy':return t('ha_sync_busy')
    from home_assistant_feedback import failure_message
    return t('ha_sync_failed')+' '+failure_message(result)

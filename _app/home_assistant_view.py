"""Read-only connected-sensor views, isolated from plant measurements."""
from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from home_assistant_archive import _check_path
from home_assistant_sensors import utc
from sensor_source_policy import hardware_id
from home_assistant_timing import timing


def plants(db_path=None):
    if db_path is None:
        from database import DB_PATH
        db_path=DB_PATH
    path=Path(db_path).resolve()
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        return db.execute('SELECT id, nom FROM plantes ORDER BY nom, id').fetchall()


def read_rows(path, mappings, *, plant_id=None, start=None, end=None, plant_db_path=None, limit=2000, metric=None):
    if type(limit) is not int or not 1 <= limit <= 10000:
        raise ValueError('invalid_limit')
    if metric is not None and metric not in ('soil_moisture','air_humidity','temperature','illuminance'):
        raise ValueError('unsupported_metric')
    path=_check_path(path,plant_db_path)
    allowed={}
    for row in mappings:
        if metric is not None and row.get('metric') != metric:
            continue
        if plant_id is not None and row.get('plant_id') != plant_id:
            continue
        allowed[(hardware_id(row.get('hardware_id')),row['metric'])]=row
    if not allowed or not path.is_file():
        return []
    begin=datetime.fromisoformat(utc(start)) if start else None
    finish=datetime.fromisoformat(utc(end)) if end else None
    if begin and finish and begin>=finish:
        raise ValueError('invalid_range')
    result=[]
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='ha_facts_v1'").fetchone():
            return []
        # Each fact may have multiple envelopes; keep a deterministic representative.
        # Conflicting versions are retained and explicitly flagged, never silently chosen.
        has_windows=db.execute("SELECT 1 FROM sqlite_master WHERE name='ha_windows_v1'").fetchone()
        boundaries={r[0] for r in db.execute('SELECT DISTINCT start_time FROM ha_windows_v1')} if has_windows else set()
        # Filter before LIMIT, including subsecond boundaries and offset-aware dates.
        def in_range(stamp):
            instant=datetime.fromisoformat(utc(stamp))
            return int((begin is None or instant>=begin) and (finish is None or instant<finish))
        time_filter=''
        if begin is not None or finish is not None:
            db.create_function('ha_in_range',1,in_range,deterministic=True)
            time_filter=' AND ha_in_range(ha_time)'
        # The global cap is applied before decoding any JSON, not once per sensor.
        pairs=' OR '.join('(physical_id=? AND metric=?)' for _ in allowed)
        parameters=[value for pair in allowed for value in pair]+[limit]
        query=('SELECT f.fact_id,f.ha_time,f.physical_id,f.metric,'
               '(SELECT count(*) FROM ha_fact_versions_v1 v WHERE v.fact_id=f.fact_id),'
               '(SELECT record_json FROM ha_envelopes_v1 e WHERE e.fact_id=f.fact_id ORDER BY observation_id LIMIT 1) '
               'FROM (SELECT fact_id,ha_time,physical_id,metric FROM ha_facts_v1 WHERE ('+pairs+')'
               +time_filter+' ORDER BY ha_time DESC,physical_id DESC,metric DESC LIMIT ?) f')
        rows=db.execute(query,parameters).fetchall()
        for fact,stamp,physical,metric,versions,raw in rows:
            instant=datetime.fromisoformat(utc(stamp))
            if (begin and instant<begin) or (finish and instant>=finish):
                continue
            if raw is None:
                continue
            record=json.loads(raw)
            evidence=timing(record,initial_state=stamp in boundaries)
            result.append({'fact_id':fact,'hardware_id':physical,'metric':metric,
                           'ha_updated_at':stamp,'value':record['value'] if versions==1 else None,
                           'unit':record['unit'],'status':record['status'] if versions==1 else 'conflict',
                           'test_data':record.get('test_data') is True,'versions':versions,**evidence})
    return sorted(result,key=lambda r:(r['ha_updated_at'],r['hardware_id'],r['metric']),reverse=True)[:limit]

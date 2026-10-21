"""Timing evidence for one quantity, never a claimed device acquisition time."""
from datetime import datetime
from home_assistant_sensors import utc


def _optional(value):
    try:
        return utc(value) if value is not None else None
    except (ValueError,TypeError):
        return None


def timing(record, *, initial_state=False):
    raw=record.get('raw_state') or {}
    updated=_optional(record.get('ha_updated_at'))
    changed=_optional(raw.get('last_changed'))
    reported=_optional(raw.get('last_reported'))
    retrieved=_optional(record.get('received_at'))
    # A report may contain a cached field; none of these proves a radio acquisition.
    kind='ha_state'
    if initial_state:
        kind='initial_state_uncertain'
    elif changed and updated and changed!=updated:
        kind='ha_attribute_update'
    elif changed and updated:
        kind='ha_value_change'
    future=bool(updated and retrieved and (datetime.fromisoformat(updated)-datetime.fromisoformat(retrieved)).total_seconds()>300)
    return dict(ha_value_changed_at=changed,ha_state_updated_at=updated,
                ha_state_reported_at=reported,gruterra_retrieved_at=retrieved,
                measured_at=None,physical_acquisition_confirmed=False,
                timing_kind=kind,usable_for_timeline=not initial_state and not future)

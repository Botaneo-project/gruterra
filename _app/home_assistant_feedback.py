"""Allowlisted, localized failure feedback; never render raw errors or payloads."""


def failure_message(result):
    from i18n import traduire_courant as t
    result = result if isinstance(result, dict) else {}
    status = result.get('http_status')
    reason = result.get('reason', result.get('code'))
    if type(status) is int and status in (401, 403):
        key = 'ha_failure_access'
    elif status == 429:
        key = 'ha_failure_rate'
    elif type(status) is int and 500 <= status <= 599:
        key = 'ha_failure_server'
    elif reason == 'history_too_large':
        key = 'ha_failure_dense'
    elif reason in ('mapping_not_authorized', 'duplicate_physical_measurement', 'source_not_authorized'):
        key = 'ha_failure_mapping'
    elif reason in ('history_connection_failed', 'connection_failed'):
        key = 'ha_failure_connection'
    else:
        key = 'ha_view_failed'
    text = t(key)
    if type(status) is int and 100 <= status <= 599:
        text += ' '+t('ha_failure_http').format(status=status)
    windows = result.get('completed_windows')
    if type(windows) is int and 0 < windows <= 1024:
        text += ' '+t('ha_failure_preserved').format(windows=windows)
    return text

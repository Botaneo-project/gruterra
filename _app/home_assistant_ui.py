"""Local configuration form. Opening/saving never contacts Home Assistant."""
from pathlib import Path
import uuid
from botaneo_config import CONFIG_DIR, lire_json, ecrire_json
from home_assistant_client import validate_config
from home_assistant_secrets import read_private, write_private
from home_assistant_registry import assess_mappings, preview
from sensor_source_policy import hardware_id

PATH = CONFIG_DIR / 'home_assistant.local.json'
METRICS = ('soil_moisture', 'air_humidity', 'temperature', 'illuminance')


def load(path=PATH):
    path = Path(path)
    if not path.exists():
        return {'schema_version': 1, 'enabled': False, 'base_url': '', 'access_token': '',
                'instance_id': '', 'max_state_age_seconds': 7200, 'entities': []}
    data = lire_json(path)
    if data.get('schema_version') != 1 or not isinstance(data.get('entities'), list):
        raise ValueError('invalid_config')
    return read_private(path)


def save_config(base_url, token, entities, path=PATH):
    if not isinstance(base_url, str) or not isinstance(token, str) or not isinstance(entities, list):
        raise ValueError('invalid_config')
    config = load(path)
    base_url, token = base_url.strip(), token.strip()
    if config.get('_secret_unavailable') and not token:
        raise ValueError('secret_replacement_required')
    # Validate optional draft connection fields without sending a request.
    instance = config.get('instance_id') or 'ha_' + uuid.uuid4().hex
    validation = {**config, 'enabled': True, 'instance_id': instance,
                  'base_url': base_url or 'https://example.invalid',
                  'access_token': token or 'draft-only',
                  'entities': entities or [{'entity_id': 'sensor.draft', 'device_id': 'draft', 'model': 'draft', 'metric': 'illuminance'}]}
    validate_config(validation)
    config.update(schema_version=1, enabled=False, instance_id=instance,
                  base_url=base_url, access_token=token, entities=entities)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_private(path, config)
    return config


def open_window(parent, palette):
    import tkinter as tk
    from tkinter import ttk
    from i18n import traduire_courant as t
    from meteo_nappes import harmoniser
    window = tk.Toplevel(parent)
    window.title(t('ha_settings_title'))
    window.geometry('850x620')
    window.minsize(620, 440)
    valid = True
    try:
        config = load()
    except (ValueError, RuntimeError, OSError):
        valid = False
        config = {'entities': []}
    rows = [dict(row) for row in config['entities'] if isinstance(row, dict)]
    # Footer remains outside the expanding table and its scrollbars.
    footer = tk.Frame(window)
    footer.pack(side='bottom', fill='x', padx=16, pady=10)
    status = tk.StringVar(value=(t('ha_secret_unavailable') if config.get('_secret_unavailable') else '') if valid else t('ha_config_unreadable'))
    tk.Label(footer, textvariable=status, anchor='w', justify='left', wraplength=560).pack(side='left', fill='x', expand=True)
    tk.Button(footer, text=t('ha_close'), command=window.destroy).pack(side='right', padx=4)
    top = tk.Frame(window)
    top.pack(fill='x', padx=16, pady=10)
    tk.Label(top, text=t('ha_settings_note'), justify='left', wraplength=780).grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
    top.columnconfigure(1, weight=1)
    variables = {}
    for row, (field, label) in enumerate((('base_url', 'ha_base_url'), ('access_token', 'ha_token')), 1):
        tk.Label(top, text=t(label)).grid(row=row, column=0, sticky='w', padx=(0, 8), pady=4)
        value = config.get(field, '')
        variables[field] = tk.StringVar(value=value if isinstance(value, str) else '')
        entry = tk.Entry(top, textvariable=variables[field], show='•' if field == 'access_token' else '')
        entry.grid(row=row, column=1, sticky='ew', pady=4)
        if field == 'access_token':
            token_entry = entry
    reveal = tk.BooleanVar(value=False)
    tk.Checkbutton(top, text=t('ha_show_token'), variable=reveal,
                   command=lambda: token_entry.configure(show='' if reveal.get() else '•')).grid(row=3, column=1, sticky='w')
    toolbar = tk.Frame(window)
    toolbar.pack(fill='x', padx=16, pady=6)
    frame = tk.Frame(window)
    frame.pack(fill='both', expand=True, padx=16)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    columns = ('entity_id', 'authorization', 'metric', 'hardware_id', 'device_id', 'model')
    table = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse', height=5)
    for key, label in zip(columns, ('ha_entity', 'ha_authorization', 'ha_metric', 'ha_hardware', 'ha_device', 'ha_model')):
        table.heading(key, text=t(label))
        table.column(key, width=180, minwidth=110, stretch=True)
    table.grid(row=0, column=0, sticky='nsew')
    vertical = ttk.Scrollbar(frame, orient='vertical', command=table.yview)
    vertical.grid(row=0, column=1, sticky='ns')
    horizontal = ttk.Scrollbar(frame, orient='horizontal', command=table.xview)
    horizontal.grid(row=1, column=0, sticky='ew')
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    def refresh():
        table.delete(*table.get_children())
        checks = assess_mappings(rows)
        for index, (row, check) in enumerate(zip(rows, checks)):
            values = [t('ha_authorization_' + check) if key == 'authorization' else t('ha_metric_' + row.get(key, '')) if key == 'metric' else row.get(key, '') for key in columns]
            table.insert('', 'end', iid=str(index), values=values)
    def edit(new=False):
        selected = table.selection()
        if not new and not selected:
            status.set(t('ha_choose_row'))
            return
        index = None if new else int(selected[0])
        original = {} if new else rows[index]
        dialog = tk.Toplevel(window)
        dialog.title(t('ha_add') if new else t('ha_edit'))
        dialog.transient(window)
        dialog.resizable(True, False)
        dialog.columnconfigure(1, weight=1)
        fields = {}
        for number, (field, label) in enumerate(zip(('entity_id', 'device_id', 'model', 'hardware_id'), ('ha_entity', 'ha_device', 'ha_model', 'ha_hardware'))):
            tk.Label(dialog, text=t(label)).grid(row=number, column=0, sticky='w', padx=12, pady=8)
            fields[field] = tk.StringVar(value=original.get(field, ''))
            tk.Entry(dialog, textvariable=fields[field], width=40).grid(row=number, column=1, sticky='ew', padx=12, pady=8)
        tk.Label(dialog, text=t('ha_metric')).grid(row=4, column=0, sticky='w', padx=12, pady=8)
        metric = ttk.Combobox(dialog, state='readonly', values=[t('ha_metric_' + key) for key in METRICS])
        metric.current(METRICS.index(original.get('metric')) if original.get('metric') in METRICS else 0)
        metric.grid(row=4, column=1, sticky='ew', padx=12, pady=8)
        confirmed = tk.BooleanVar(value=original.get('hardware_confirmed') is True)
        tk.Checkbutton(dialog, text=t('ha_confirm_hardware'), variable=confirmed, wraplength=430, justify='left').grid(row=5, column=0, columnspan=2, sticky='w', padx=12, pady=8)
        message = tk.StringVar()
        tk.Label(dialog, textvariable=message, wraplength=460).grid(row=6, column=0, columnspan=2, padx=12)
        def accept():
            row = {key: variable.get().strip() for key, variable in fields.items()}
            row['metric'] = METRICS[metric.current()]
            row['hardware_confirmed'] = confirmed.get()
            if row['hardware_id']:
                try:
                    row['hardware_id'] = hardware_id(row['hardware_id'])
                except ValueError:
                    message.set(t('ha_hardware_invalid'))
                    return
            elif row['hardware_confirmed']:
                message.set(t('ha_hardware_invalid'))
                return
            proposed = list(rows)
            if index is None:
                proposed.append(row)
            else:
                proposed[index] = row
            try:
                validate_config({'schema_version': 1, 'enabled': True, 'base_url': 'https://example.invalid', 'access_token': 'draft-only', 'instance_id': 'draft', 'entities': proposed})
            except ValueError:
                message.set(t('ha_invalid_mapping'))
                return
            rows[:] = proposed
            refresh()
            status.set(t('ha_unsaved'))
            dialog.destroy()
        tk.Button(dialog, text=t('ha_accept'), command=accept).grid(row=7, column=1, sticky='e', padx=12, pady=12)
        harmoniser(dialog, palette)
        dialog.grab_set()
    def remove():
        selected = table.selection()
        if selected:
            del rows[int(selected[0])]
            refresh()
            status.set(t('ha_unsaved'))
    for label, command in (('ha_add', lambda: edit(True)), ('ha_edit', edit), ('ha_remove', remove)):
        tk.Button(toolbar, text=t(label), command=command).pack(side='left', padx=(0, 8))
    is_demo = __import__('os').environ.get('BOTANEO_DEMO') == '1'
    def show_preview():
        import threading
        from queue import Queue, Empty
        from datetime import datetime, timezone
        status.set(t('ha_preview_loading'))
        preview_button.configure(state='disabled')
        pending = Queue()
        selected_rows = [dict(row) for row in rows]
        draft = {**config, 'base_url': variables['base_url'].get().strip(), 'access_token': variables['access_token'].get().strip()}
        # An unsaved new profile has no stable instance identity yet.
        if not is_demo and not draft.get('instance_id'):
            status.set(t('ha_preview_save_first'))
            preview_button.configure(state='normal')
            return
        def worker():
            try:
                if is_demo:
                    from home_assistant_demo import preview as fictional_preview
                    result = fictional_preview()
                else:
                    result = preview(draft, selected_rows, received_at=datetime.now(timezone.utc).isoformat())
            except Exception:
                result = {'ok': False, 'code': 'connection_failed', 'http_status': None, 'records': []}
            pending.put(result)
        def poll():
            if not window.winfo_exists():
                return
            try:
                result = pending.get_nowait()
            except Empty:
                window.after(100, poll)
                return
            preview_button.configure(state='normal')
            refresh()
            if not result.get('ok'):
                key = 'ha_preview_blocked' if result.get('code') == 'mapping_not_authorized' else 'ha_preview_failed'
                status.set(t(key))
                return
            status.set(t('ha_demo_ready' if is_demo else 'ha_preview_ready'))
            dialog = tk.Toplevel(window)
            dialog.title(t('ha_demo_preview_title' if is_demo else 'ha_preview_title'))
            dialog.geometry('900x420')
            tk.Label(dialog, text=t('ha_demo_preview_note' if is_demo else 'ha_preview_note'), wraplength=820, justify='left').pack(fill='x', padx=12, pady=10)
            tk.Button(dialog, text=t('ha_close'), command=dialog.destroy).pack(side='bottom', anchor='e', padx=12, pady=10)
            grid = tk.Frame(dialog)
            grid.pack(fill='both', expand=True, padx=12)
            grid.columnconfigure(0, weight=1)
            grid.rowconfigure(0, weight=1)
            names = ('entity', 'value', 'unit', 'date', 'status', 'freshness')
            view = ttk.Treeview(grid, columns=names, show='headings')
            for column, key in zip(names, ('ha_entity', 'ha_preview_value', 'ha_preview_unit', 'ha_preview_date', 'ha_preview_state', 'ha_preview_freshness')):
                view.heading(column, text=t(key))
                view.column(column, width=160, minwidth=100)
            view.grid(row=0, column=0, sticky='nsew')
            scroll = ttk.Scrollbar(grid, orient='vertical', command=view.yview)
            scroll.grid(row=0, column=1, sticky='ns')
            hscroll = ttk.Scrollbar(grid, orient='horizontal', command=view.xview)
            hscroll.grid(row=1, column=0, sticky='ew')
            view.configure(yscrollcommand=scroll.set, xscrollcommand=hscroll.set)
            for row in result['records']:
                view.insert('', 'end', values=(row['entity_id'], row['value'] if row['value'] is not None else '—', row['unit'] or '—', row['ha_updated_at'] or '—', t('ha_state_' + row['status']), t('ha_freshness_' + row['state_time_quality'])))
            harmoniser(dialog, palette)
        threading.Thread(target=worker, daemon=True).start()
        window.after(100, poll)
    preview_button = tk.Button(toolbar, text=t('ha_demo_preview_button' if is_demo else 'ha_preview_button'), command=show_preview)
    preview_button.pack(side='left', padx=(0, 8))
    from home_assistant_catchup_ui import open_window as open_catchup
    tk.Button(top, text=t('ha_catchup_title'), command=lambda:open_catchup(window, palette)).grid(row=4, column=1, sticky='w', pady=8)
    def save():
        try:
            saved = save_config(variables['base_url'].get(), variables['access_token'].get(), rows)
            config.update(saved)
        except ValueError as error:
            key = {
                'invalid_url': 'ha_error_url', 'https_required': 'ha_error_url',
                'invalid_credentials': 'ha_error_token_format',
                'invalid_mapping': 'ha_error_mapping', 'device_mapping_required': 'ha_error_mapping',
                'unsupported_metric': 'ha_error_mapping', 'invalid_entity': 'ha_error_mapping',
                'entities_required': 'ha_error_mapping',
                'secret_replacement_required': 'ha_secret_unavailable',
                'secure_storage_unavailable': 'ha_error_secure_storage',
                'secret_unavailable': 'ha_error_secure_storage',
            }.get(str(error), 'ha_save_failed')
            status.set(t(key))
            return
        except OSError:
            status.set(t('ha_error_file_write'))
            return
        except RuntimeError:
            status.set(t('ha_error_file_write'))
            return
        status.set(t('ha_saved'))
    tk.Button(footer, text=t('ha_save'), command=save, state='normal' if valid else 'disabled').pack(side='right', padx=4)
    refresh()
    harmoniser(window, palette)
    return window

"""Local configuration form. Opening/saving never contacts Home Assistant."""
from pathlib import Path
import uuid
import os
from botaneo_config import CONFIG_DIR, lire_json, ecrire_json
from home_assistant_client import validate_config
from home_assistant_secrets import read_private, write_private
from home_assistant_registry import assess_mappings, preview
from sensor_source_policy import hardware_id

PATH = CONFIG_DIR / 'home_assistant.local.json'
METRICS = ('soil_moisture', 'air_humidity', 'temperature', 'illuminance')


def load(path=PATH):
    if os.environ.get('BOTANEO_DEMO') == '1':
        return {'schema_version':1,'enabled':False,'base_url':'','access_token':'','instance_id':'','entities':[]}
    path = Path(path)
    if not path.exists():
        return {'schema_version': 1, 'enabled': False, 'base_url': '', 'access_token': '',
                'instance_id': '', 'max_state_age_seconds': 7200, 'entities': []}
    data = lire_json(path)
    if data.get('schema_version') != 1 or not isinstance(data.get('entities'), list):
        raise ValueError('invalid_config')
    return read_private(path)


def save_config(base_url, token, entities, path=PATH, *, sync_on_request=None, plant_db_path=None):
    if os.environ.get('BOTANEO_DEMO') == '1':
        raise ValueError('demo_disabled')
    if not isinstance(base_url, str) or not isinstance(token, str) or not isinstance(entities, list):
        raise ValueError('invalid_config')
    if sync_on_request is not None and type(sync_on_request) is not bool:
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
    sync_enabled = sync_on_request if sync_on_request is not None else config.get('sync_on_request') is True
    if sync_enabled:
        if not base_url or not token:
            raise ValueError('sync_connection_required')
        if not entities:
            raise ValueError('sync_entities_required')
        validate_config({**validation, 'base_url':base_url, 'access_token':token, 'entities':entities})
        checks = assess_mappings(entities, db_path=plant_db_path)
        for blocked in ('registry_unavailable','already_ble','duplicate','identity_pending'):
            if blocked in checks:
                raise ValueError('sync_'+blocked)
        from home_assistant_registry import authorized_selection
        authorized_selection(entities, db_path=plant_db_path)
    config.update(schema_version=1, enabled=False, instance_id=instance,
                  base_url=base_url, access_token=token, entities=entities)
    if sync_on_request is not None:
        if type(sync_on_request) is not bool:
            raise ValueError('invalid_config')
        config['sync_on_request'] = sync_on_request
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_private(path, config)
    return config


def open_window(parent, palette):
    import tkinter as tk
    from tkinter import ttk
    from i18n import traduire_courant as t
    from ui_scroll_form import create
    from meteo_nappes import harmoniser
    window = tk.Toplevel(parent)
    window.title(t('ha_settings_title'))
    window.geometry('850x620')
    window.minsize(620, 440)
    valid = True
    is_demo = os.environ.get('BOTANEO_DEMO') == '1'
    try:
        if is_demo:
            from home_assistant_demo import preview as demo_preview
            config={'entities':[{key:row[key] for key in ('entity_id','device_id','model','hardware_id','metric','test_data')} for row in demo_preview()['records']]}
        else:
            config = load()
    except (ValueError, RuntimeError, OSError):
        valid = False
        config = {'entities': []}
    rows = [dict(row) for row in config['entities'] if isinstance(row, dict)]
    # Footer remains outside the expanding table and its scrollbars.
    body, footer = create(window, palette)
    footer.columnconfigure(0, weight=1)
    status = tk.StringVar(value=t('ha_demo_settings') if is_demo else ((t('ha_secret_unavailable') if config.get('_secret_unavailable') else '') if valid else t('ha_config_unreadable')))
    tk.Label(footer, textvariable=status, anchor='w', justify='left', wraplength=560).grid(row=0, column=0, columnspan=2, sticky='ew')
    tk.Button(footer, text=t('ha_close'), command=window.destroy).grid(row=1, column=1, sticky='e', padx=4)
    top = tk.Frame(body)
    top.pack(fill='x', padx=16, pady=10)
    tk.Label(top, text=t('ha_settings_note'), justify='left', wraplength=780).grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
    top.columnconfigure(1, weight=1)
    def resize_top(event):
        for child in top.winfo_children():
            if isinstance(child, tk.Label): child.configure(wraplength=max(160,event.width-16))
    top.bind('<Configure>', resize_top)
    variables = {}
    for row, (field, label) in enumerate((('base_url', 'ha_base_url'), ('access_token', 'ha_token')), 1):
        tk.Label(top, text=t(label)).grid(row=row, column=0, sticky='w', padx=(0, 8), pady=4)
        value = config.get(field, '')
        variables[field] = tk.StringVar(value=value if isinstance(value, str) else '')
        entry = tk.Entry(top, textvariable=variables[field], show='•' if field == 'access_token' else '',state='disabled' if is_demo else 'normal')
        entry.grid(row=row, column=1, sticky='ew', pady=4)
        if field == 'access_token':
            token_entry = entry
    reveal = tk.BooleanVar(value=False)
    tk.Checkbutton(top, text=t('ha_show_token'), variable=reveal,state='disabled' if is_demo else 'normal',
                   command=lambda: token_entry.configure(show='' if reveal.get() else '•')).grid(row=3, column=1, sticky='w')
    toolbar = tk.Frame(body)
    toolbar.pack(fill='x', padx=16, pady=6)
    frame = tk.Frame(body)
    frame.pack(fill='both', expand=True, padx=16)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    columns = ('plant', 'metric', 'authorization', 'entity_id', 'hardware_id', 'device_id', 'model')
    table = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse', height=5)
    for key, label in zip(columns, ('ha_view_plant', 'ha_metric', 'ha_authorization', 'ha_entity', 'ha_hardware', 'ha_device', 'ha_model')):
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
        checks = ['demo']*len(rows) if is_demo else assess_mappings(rows)
        from home_assistant_view import plants
        try:
            plant_names = {} if is_demo else dict(plants())
        except Exception:
            plant_names = {}
        for index, (row, check) in enumerate(zip(rows, checks)):
            pid = row.get('plant_id')
            plant_name = t('ha_view_unassigned') if pid is None else plant_names.get(pid,t('ha_association_missing').format(id=pid))
            values = [plant_name if key == 'plant' else t('ha_authorization_' + check) if key == 'authorization' else t('ha_metric_' + row.get(key, '')) if key == 'metric' else row.get(key, '') for key in columns]
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
        dialog.geometry('650x640')
        dialog.minsize(520,400)
        dialog.resizable(True, True)
        form, actions = create(dialog,palette)
        form.columnconfigure(1, weight=1)
        fields = {}
        for number, (field, label) in enumerate(zip(('entity_id', 'device_id', 'model', 'hardware_id'), ('ha_entity', 'ha_device', 'ha_model', 'ha_hardware'))):
            tk.Label(form, text=t(label)).grid(row=number, column=0, sticky='w', padx=12, pady=8)
            fields[field] = tk.StringVar(value=original.get(field, ''))
            tk.Entry(form, textvariable=fields[field], width=40).grid(row=number, column=1, sticky='ew', padx=12, pady=8)
        tk.Label(form, text=t('ha_metric')).grid(row=4, column=0, sticky='w', padx=12, pady=8)
        metric = ttk.Combobox(form, state='readonly', values=[t('ha_metric_' + key) for key in METRICS])
        metric.current(METRICS.index(original.get('metric')) if original.get('metric') in METRICS else 0)
        metric.grid(row=4, column=1, sticky='ew', padx=12, pady=8)
        confirmed = tk.BooleanVar(value=original.get('hardware_confirmed') is True)
        tk.Checkbutton(form, text=t('ha_confirm_hardware'), variable=confirmed, wraplength=430, justify='left').grid(row=5, column=0, columnspan=2, sticky='w', padx=12, pady=8)
        test_data = tk.BooleanVar(value=original.get('test_data', False))
        tk.Checkbutton(form, text=t('ha_test_data'), variable=test_data).grid(row=6, column=0, columnspan=2, sticky='w', padx=12, pady=6)
        message = tk.StringVar()
        tk.Label(form, textvariable=message, wraplength=460).grid(row=7, column=0, columnspan=2, padx=12)
        from home_assistant_view import plants
        try:
            available_plants = [] if is_demo else plants()
        except Exception:
            available_plants = []
        plant_values = [t('ha_view_unassigned')] + [str(pid)+' — '+name for pid,name in available_plants]
        plant_ids = [None] + [pid for pid,_ in available_plants]
        tk.Label(form,text=t('ha_view_plant')).grid(row=8,column=0,sticky='w',padx=12)
        plant = ttk.Combobox(form,state='readonly',values=plant_values,width=40)
        plant.current(plant_ids.index(original.get('plant_id')) if original.get('plant_id') in plant_ids else 0)
        plant.grid(row=8,column=1,sticky='ew',padx=12,pady=6)
        def accept():
            row = {**original, **{key: variable.get().strip() for key, variable in fields.items()}}
            row['plant_id'] = plant_ids[plant.current()]
            row['metric'] = METRICS[metric.current()]
            row['hardware_confirmed'] = confirmed.get()
            row['test_data'] = test_data.get()
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
        tk.Button(actions, text=t('ha_accept'), command=accept).pack(side='right', padx=12, pady=12)
        harmoniser(dialog, palette)
        dialog.grab_set()
    def remove():
        selected = table.selection()
        if selected:
            del rows[int(selected[0])]
            refresh()
            status.set(t('ha_unsaved'))
    for label, command in (('ha_add', lambda: edit(True)), ('ha_edit', edit), ('ha_remove', remove)):
        tk.Button(toolbar, text=t(label), command=command,state='disabled' if is_demo else 'normal').pack(anchor='w', pady=3)
    def show_preview():
        import threading
        from queue import Queue
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
        def finished(result):
            preview_button.configure(state='normal')
            refresh()
            if not result.get('ok'):
                from home_assistant_feedback import failure_message
                status.set(failure_message(result))
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
            names = ('entity', 'value', 'unit', 'date', 'retrieved', 'status', 'freshness')
            view = ttk.Treeview(grid, columns=names, show='headings')
            for column, key in zip(names, ('ha_entity', 'ha_preview_value', 'ha_preview_unit', 'ha_timing_state_date', 'ha_timing_retrieved', 'ha_preview_state', 'ha_preview_freshness')):
                view.heading(column, text=t(key))
                view.column(column, width=160, minwidth=100)
            view.grid(row=0, column=0, sticky='nsew')
            scroll = ttk.Scrollbar(grid, orient='vertical', command=view.yview)
            scroll.grid(row=0, column=1, sticky='ns')
            hscroll = ttk.Scrollbar(grid, orient='horizontal', command=view.xview)
            hscroll.grid(row=1, column=0, sticky='ew')
            view.configure(yscrollcommand=scroll.set, xscrollcommand=hscroll.set)
            for row in result['records']:
                view.insert('', 'end', values=(row['entity_id'], row['value'] if row['value'] is not None else '—', row['unit'] or '—', row['ha_updated_at'] or '—', row['received_at'], t('ha_state_' + row['status']), t('ha_freshness_' + row['state_time_quality'])))
            harmoniser(dialog, palette)
        threading.Thread(target=worker, daemon=True).start()
        from ui_async_result import deliver
        deliver(window,pending,finished)
    preview_button = tk.Button(toolbar, text=t('ha_demo_preview_button' if is_demo else 'ha_preview_button'), command=show_preview)
    preview_button.pack(anchor='w', pady=3)
    from home_assistant_catchup_ui import open_window as open_catchup
    tk.Button(top, text=t('ha_catchup_title'),state='disabled' if is_demo else 'normal', command=lambda:open_catchup(window, palette)).grid(row=4, column=1, sticky='w', pady=8)
    from home_assistant_dashboard import open_window as open_sensors
    tk.Button(toolbar, text=t('ha_view_title'), command=lambda:open_sensors(window, palette)).pack(anchor='w', pady=3)
    from home_assistant_test_ui import open_window as open_tests
    tk.Button(toolbar, text=t('ha_test_title'), command=lambda:open_tests(window, palette)).pack(anchor='w', pady=3)
    sync_requested = tk.BooleanVar(value=config.get('sync_on_request') is True)
    tk.Checkbutton(toolbar, text=t('ha_sync_enable'), variable=sync_requested,state='disabled' if is_demo else 'normal', wraplength=600, justify='left').pack(anchor='w', pady=6)
    def save():
        if is_demo:
            status.set(t('ha_demo_settings'));return
        try:
            saved = save_config(variables['base_url'].get(), variables['access_token'].get(), rows, sync_on_request=sync_requested.get())
            config.update(saved)
        except ValueError as error:
            key = {
                'invalid_url': 'ha_error_url', 'https_required': 'ha_error_url',
                'invalid_credentials': 'ha_error_token_format',
                'invalid_mapping': 'ha_error_mapping', 'device_mapping_required': 'ha_error_mapping',
                'unsupported_metric': 'ha_error_mapping', 'invalid_entity': 'ha_error_mapping',
                'entities_required': 'ha_error_mapping',
                'sync_connection_required':'ha_sync_connection_required',
                'sync_entities_required':'ha_sync_entities_required',
                'sync_registry_unavailable':'ha_sync_registry_unavailable',
                'sync_already_ble':'ha_sync_already_ble',
                'sync_duplicate':'ha_sync_duplicate',
                'sync_identity_pending':'ha_sync_identity_pending',
                'mapping_not_authorized':'ha_failure_mapping',
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
        from ui_data_events import notifier_associations_modifiees
        notifier_associations_modifiees(window._root())
    tk.Button(footer, text=t('ha_save'), command=save, state='normal' if valid and not is_demo else 'disabled').grid(row=1, column=0, sticky='w', padx=4)
    footer.bind('<Configure>', lambda event: [child.configure(wraplength=max(160,event.width-16)) for child in footer.winfo_children() if isinstance(child,tk.Label)])
    refresh()
    harmoniser(window, palette)
    return window

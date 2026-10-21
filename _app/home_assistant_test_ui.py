"""Local test archive management; no network, credentials or plant DB writes."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def date_range(start, end):
    """Inclusive calendar dates, interpreted in Europe/Paris, DST included."""
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last:
        raise ValueError('invalid_purge_range')
    zone = ZoneInfo('Europe/Paris')
    return (datetime.combine(first, time.min, zone).isoformat(),
            datetime.combine(last+timedelta(days=1), time.min, zone).isoformat())


def open_window(parent, palette, *, archive_path=None, mappings=None):
    import os
    import tkinter as tk
    from tkinter import ttk, messagebox
    from pathlib import Path
    from queue import Queue, Empty
    import threading
    from botaneo_config import DATA_DIR
    from home_assistant_ui import load
    from home_assistant_test_data import preview_test_purge, purge_test_data
    from sensor_source_policy import hardware_id
    from ui_scroll_form import create, create_text
    from meteo_nappes import harmoniser
    from i18n import traduire_courant as t
    window = tk.Toplevel(parent)
    window.title(t('ha_test_title'))
    window.geometry('760x540')
    window.minsize(560, 390)
    body, footer = create(window, palette)
    footer.columnconfigure(0, weight=1)
    current = {}
    archive = Path(archive_path) if archive_path is not None else Path(DATA_DIR)/'home_assistant_history.sqlite3'
    demo = os.environ.get('BOTANEO_DEMO') == '1'
    devices = {}
    try:
        rows = [] if demo else (mappings if mappings is not None else load()['entities'])
        for row in rows:
            if row.get('test_data') is True:
                physical = hardware_id(row.get('hardware_id'))
                devices[physical] = row.get('model', '')
    except Exception:
        devices = {}
    top = tk.Frame(body)
    top.pack(fill='x', padx=16, pady=12)
    note = tk.Label(top, text=t('ha_test_note'), wraplength=620, justify='left')
    note.pack(fill='x')
    top.bind('<Configure>', lambda e: note.configure(wraplength=max(160,e.width-12)))
    tk.Label(top, text=t('ha_test_device')).pack(anchor='w', pady=(10,0))
    identities = list(devices)
    selector = ttk.Combobox(top, state='readonly', values=[devices[key]+' — '+key for key in identities], width=55)
    selector.pack(fill='x')
    if identities:
        selector.current(0)
    dates = []
    today = datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()
    for key in ('ha_test_start', 'ha_test_end'):
        tk.Label(top, text=t(key)).pack(anchor='w', pady=(8,0))
        value = tk.StringVar(value=today)
        tk.Entry(top, textvariable=value).pack(fill='x')
        dates.append(value)
    report = create_text(body, palette, height=8, padx=16, pady=10)
    def show(text):
        report.configure(state='normal')
        report.delete('1.0','end')
        report.insert('1.0', text)
        report.configure(state='disabled')
    def invalidate(*args):
        current.clear()
        remove.configure(state='disabled')
    for value in dates:
        value.trace_add('write', invalidate)
    selector.bind('<<ComboboxSelected>>', invalidate)
    def job(function, done):
        pending = Queue()
        preview.configure(state='disabled')
        remove.configure(state='disabled')
        selector.configure(state='disabled')
        def worker():
            try:
                pending.put((True,function()))
            except Exception:
                pending.put((False,None))
        def poll():
            if not window.winfo_exists():
                return
            try:
                ok,result = pending.get_nowait()
            except Empty:
                window.after(100,poll)
                return
            preview.configure(state='normal' if identities and not demo else 'disabled')
            selector.configure(state='readonly')
            if ok:
                done(result)
            else:
                current.clear()
                show(t('ha_test_failed'))
        threading.Thread(target=worker,daemon=True).start()
        window.after(100,poll)
    def prepare():
        invalidate()
        if not identities or demo:
            return
        try:
            start,end = date_range(*(value.get().strip() for value in dates))
        except (ValueError,OverflowError):
            show(t('ha_test_dates_invalid'))
            return
        physical = identities[selector.current()]
        chosen = tuple(value.get() for value in dates)
        def ready(plan):
            if chosen != tuple(value.get() for value in dates):
                show(t('ha_test_changed'))
                return
            current['plan'] = plan
            show(t('ha_test_summary').format(device=physical, facts=plan['facts'], envelopes=plan['envelopes']))
            remove.configure(state='normal' if plan['facts'] else 'disabled')
        job(lambda:preview_test_purge(archive,physical,start=start,end=end),ready)
    def confirm():
        plan = current.get('plan')
        if not plan or demo:
            return
        if not messagebox.askyesno(t('ha_test_title'),t('ha_test_confirm').format(device=plan['physical_id'],facts=plan['facts']),parent=window):
            return
        invalidate()
        show(t('ha_test_running'))
        def done(result):
            from ui_data_events import notifier_donnees_modifiees
            notifier_donnees_modifiees(parent.winfo_toplevel())
            show(t('ha_test_done').format(facts=result['facts_deleted'],backup=result['backup']))
        job(lambda:purge_test_data(archive,plan,confirmed=True),done)
    preview = tk.Button(top,text=t('ha_test_preview'),command=prepare,state='normal' if identities and not demo else 'disabled')
    preview.pack(anchor='w',pady=10)
    remove = tk.Button(footer,text=t('ha_test_remove'),command=confirm,state='disabled')
    remove.grid(row=0,column=0,sticky='ew')
    tk.Button(footer,text=t('ha_close'),command=window.destroy).grid(row=1,column=0,sticky='e',pady=8)
    show(t('ha_test_demo') if demo else t('ha_test_initial') if identities else t('ha_test_no_device'))
    harmoniser(window,palette)
    return window

"""Manual catch-up plan and confirmation UI; no automatic activation."""
from datetime import datetime, timedelta, timezone
from pathlib import Path


def open_window(parent, palette):
    import tkinter as tk
    from tkinter import ttk
    from queue import Queue
    import threading
    from botaneo_config import DATA_DIR
    from home_assistant_ui import load
    from home_assistant_archive import checkpoint
    from home_assistant_catchup import plan_catchup, run_catchup
    from i18n import traduire_courant as t
    from ui_scroll_form import create, create_text
    from meteo_nappes import harmoniser
    window = tk.Toplevel(parent)
    window.title(t('ha_catchup_title'))
    window.geometry('760x490')
    window.minsize(620, 420)
    archive = Path(DATA_DIR)/'home_assistant_history.sqlite3'
    demo = __import__('os').environ.get('BOTANEO_DEMO') == '1'
    current = {}
    body, footer = create(window, palette)
    footer.columnconfigure(0, weight=1)
    tk.Button(footer, text=t('ha_close'), command=window.destroy).grid(row=1, column=0, sticky='e', pady=(6, 0))
    top = tk.Frame(body)
    top.pack(fill='x', padx=16, pady=12)
    note = tk.Label(top, text=t('ha_catchup_note'), wraplength=540, justify='left')
    note.pack(fill='x', pady=(0, 12))
    top.bind('<Configure>', lambda event: note.configure(wraplength=max(160, event.width-8)))
    period = ttk.Combobox(top, state='readonly', values=[t('ha_catchup_day'), t('ha_catchup_week')])
    period.current(0)
    period.pack(anchor='w')
    summary = tk.StringVar(value=t('ha_demo_settings') if demo else t('ha_catchup_initial'))
    report = create_text(body, palette, height=9, padx=16, pady=12)
    def show_summary(*args):
        report.configure(state='normal')
        report.delete('1.0', 'end')
        report.insert('1.0', summary.get())
        report.configure(state='disabled')
    summary.trace_add('write', show_summary)
    show_summary()
    def invalidate(event=None):
        current.clear()
        confirm_button.configure(state='disabled')
        summary.set(t('ha_catchup_initial'))
    period.bind('<<ComboboxSelected>>', invalidate)
    def plan():
        if demo:
            summary.set(t('ha_demo_settings'));return
        invalidate()
        try:
            config = load()
            now = datetime.now(timezone.utc)
            start = now-timedelta(days=1 if period.current() == 0 else 7)
            saved = checkpoint(archive, config)
            if saved:
                start = min(start, datetime.fromisoformat(saved))
            target = min(now,start+timedelta(days=7))
            prepared = plan_catchup(config, archive, start=start.isoformat(), end=target.isoformat(), received_at=now.isoformat())
            current.update(config=config, plan=prepared, more=target < now)
            if not prepared['windows']:
                summary.set(t('ha_catchup_nothing'))
                return
            summary.set(t('ha_catchup_summary').format(count=len(prepared['windows']), start=prepared['windows'][0]['start'], end=prepared['windows'][-1]['end']))
            confirm_button.configure(state='normal')
        except Exception:
            summary.set(t('ha_catchup_plan_failed'))
    def confirm():
        if demo or not current:
            return
        config, prepared = current['config'], current['plan']
        more = current.get('more',False)
        confirm_button.configure(state='disabled')
        plan_button.configure(state='disabled')
        period.configure(state='disabled')
        summary.set(t('ha_catchup_running'))
        pending = Queue()
        def worker():
            try:
                archive.parent.mkdir(parents=True, exist_ok=True)
                result = run_catchup(config, prepared, archive, confirmed=True, received_at=datetime.now(timezone.utc).isoformat())
                if result.get('ok') and more:
                    result={**result,'code':'more_pending'}
            except Exception:
                result = {'ok': False, 'code': 'catchup_interrupted', 'completed_windows': 0}
            pending.put(result)
        def finished(result):
            current.clear()
            plan_button.configure(state='normal')
            period.configure(state='readonly')
            if result.get('ok'):
                summary.set(t('ha_catchup_done').format(windows=result['completed_windows'], facts=result['facts_added'], revisions=result['revisions_added'], duplicates=result['duplicates']) + ('\n'+t('ha_catchup_more') if result['code'] == 'more_pending' else ''))
            else:
                from home_assistant_feedback import failure_message
                summary.set(failure_message(result))
        event_root=window._root()
        def published(result):
            if result.get('ok') or result.get('completed_windows',0):
                from ui_data_events import notifier_donnees_modifiees
                notifier_donnees_modifiees(event_root,exclude=window)
        threading.Thread(target=worker, daemon=True).start()
        from ui_async_result import deliver
        deliver(window,pending,finished,on_result=published,keep_after_close=True)
    confirm_button = tk.Button(footer, text=t('ha_catchup_confirm'), command=confirm, state='disabled')
    confirm_button.grid(row=0, column=0, sticky='ew')
    plan_button = tk.Button(top, text=t('ha_catchup_plan'), command=plan,state='disabled' if demo else 'normal')
    plan_button.pack(anchor='w', pady=12)
    harmoniser(window, palette)
    return window

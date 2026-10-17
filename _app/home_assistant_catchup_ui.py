"""Manual catch-up plan and confirmation UI; no automatic activation."""
from datetime import datetime, timedelta, timezone
from pathlib import Path


def open_window(parent, palette):
    import tkinter as tk
    from tkinter import ttk
    from queue import Queue, Empty
    import threading
    from botaneo_config import APP_DIR
    from home_assistant_ui import load
    from home_assistant_archive import checkpoint
    from home_assistant_catchup import plan_catchup, run_catchup
    from i18n import traduire_courant as t
    from meteo_nappes import harmoniser
    window = tk.Toplevel(parent)
    window.title(t('ha_catchup_title'))
    window.geometry('760x490')
    window.minsize(620, 420)
    archive = Path(APP_DIR)/'data/home_assistant_history.sqlite3'
    current = {}
    footer = tk.Frame(window)
    footer.pack(side='bottom', fill='x', padx=16, pady=12)
    tk.Button(footer, text=t('ha_close'), command=window.destroy).pack(side='right', padx=4)
    top = tk.Frame(window)
    top.pack(fill='x', padx=16, pady=12)
    tk.Label(top, text=t('ha_catchup_note'), wraplength=690, justify='left').pack(fill='x', pady=(0, 12))
    period = ttk.Combobox(top, state='readonly', values=[t('ha_catchup_day'), t('ha_catchup_week')])
    period.current(0)
    period.pack(anchor='w')
    summary = tk.StringVar(value=t('ha_catchup_initial'))
    tk.Label(window, textvariable=summary, justify='left', anchor='nw', wraplength=690).pack(fill='both', expand=True, padx=16, pady=12)
    def invalidate(event=None):
        current.clear()
        confirm_button.configure(state='disabled')
        summary.set(t('ha_catchup_initial'))
    period.bind('<<ComboboxSelected>>', invalidate)
    def plan():
        invalidate()
        try:
            config = load()
            now = datetime.now(timezone.utc)
            start = now-timedelta(days=1 if period.current() == 0 else 7)
            saved = checkpoint(archive, config)
            if saved:
                start = min(start, datetime.fromisoformat(saved))
            prepared = plan_catchup(config, archive, start=start.isoformat(), end=now.isoformat(), received_at=now.isoformat())
            current.update(config=config, plan=prepared)
            if not prepared['windows']:
                summary.set(t('ha_catchup_nothing'))
                return
            summary.set(t('ha_catchup_summary').format(count=len(prepared['windows']), start=prepared['windows'][0]['start'], end=prepared['windows'][-1]['end']))
            confirm_button.configure(state='normal')
        except Exception:
            summary.set(t('ha_catchup_plan_failed'))
    def confirm():
        if not current:
            return
        config, prepared = current['config'], current['plan']
        confirm_button.configure(state='disabled')
        plan_button.configure(state='disabled')
        period.configure(state='disabled')
        summary.set(t('ha_catchup_running'))
        pending = Queue()
        def worker():
            try:
                archive.parent.mkdir(parents=True, exist_ok=True)
                result = run_catchup(config, prepared, archive, confirmed=True, received_at=datetime.now(timezone.utc).isoformat())
            except Exception:
                result = {'ok': False, 'code': 'catchup_interrupted', 'completed_windows': 0}
            pending.put(result)
        def poll():
            if not window.winfo_exists():
                return
            try:
                result = pending.get_nowait()
            except Empty:
                window.after(100, poll)
                return
            current.clear()
            plan_button.configure(state='normal')
            period.configure(state='readonly')
            if result.get('ok'):
                summary.set(t('ha_catchup_done').format(windows=result['completed_windows'], facts=result['facts_added'], revisions=result['revisions_added'], duplicates=result['duplicates']) + ('\n'+t('ha_catchup_more') if result['code'] == 'more_pending' else ''))
            else:
                summary.set(t('ha_catchup_failed').format(windows=result.get('completed_windows', 0)))
        threading.Thread(target=worker, daemon=True).start()
        window.after(100, poll)
    confirm_button = tk.Button(footer, text=t('ha_catchup_confirm'), command=confirm, state='disabled')
    confirm_button.pack(side='right', padx=4)
    plan_button = tk.Button(top, text=t('ha_catchup_plan'), command=plan)
    plan_button.pack(anchor='w', pady=12)
    harmoniser(window, palette)
    return window

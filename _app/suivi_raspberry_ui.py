"""Carte Tkinter ; seul le thread principal manipule les widgets."""

from i18n import traduire_courant as _tr
import raspberry_sync
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from pathlib import Path
from suivi_raspberry import Store, load_config, save_config, deadline, is_due, probe, status, local_date, now_utc


class SuiviRaspberry:
    def __init__(self, root, config_dir, data_dir):
        self.root = root
        self.path = Path(config_dir) / 'raspberry.local.json'
        self.store = Store(Path(data_dir) / 'raspberry_sync_suivi.sqlite3')
        self.next_attempt = None
        self.last_result = None
        self.last_pending = None
        self.busy = False
        self.queue = queue.Queue()
        self.detail = tk.StringVar(root)
        self.title = tk.StringVar(root)
        self.buttons = []
        self.config = None
        self.config_error = None
        self.runtime_error = None
        self.reload()

    def reload(self):
        try:
            self.config = load_config(self.path)
            self.config_error = None
        except (OSError, ValueError):
            self.config = None
            self.config_error = 'Configuration Raspberry absente ou invalide.'

    def start(self):
        self.tick()

    def tick(self):
        try:
            while True:
                error = self.queue.get_nowait()
                self.busy = False
                self.runtime_error = error
        except queue.Empty:
            pass
        try:
            if (self.config and self.config['enabled'] and not self.config['away']
                    and not self.busy and (self.next_attempt is None or now_utc() >= self.next_attempt)):
                self.check()
            self.render()
        except Exception:
            # Ne jamais arrêter la boucle Tkinter ni révéler d'exception contenant des chemins.
            self.runtime_error = _tr('suivi_raspberry_ui_text_56')
            self.title.set(self.runtime_error)
        self.root.after(5000, self.tick)

    def check(self):
        if self.busy or not self.config:
            return
        self.next_attempt = now_utc() + timedelta(minutes=self.config['retry_minutes'])
        self.busy = True
        self.runtime_error = None
        config = dict(self.config)
        due = deadline(config)
        def worker():
            error = None
            try:
                result = raspberry_sync.synchronize(config)
                ok, reason = result['ok'], result['message']
                self.last_result = reason
                self.last_pending = result.get('pending_remaining')
                self.store.record(ok, reason, due)
            except Exception:
                error = _tr('suivi_raspberry_ui_text_77')
            self.queue.put(error)
        threading.Thread(target=worker, daemon=True).start()

    def render(self):
        if not self.config:
            self.title.set(self.config_error)
            self.detail.set(_tr('suivi_raspberry_ui_text_84'))
            return
        state = self.store.read()
        self.title.set(self.runtime_error or (_tr('suivi_raspberry_ui_text_87') if self.busy else status(self.config, state)))
        next_at = local_date(self.next_attempt.isoformat()) if self.next_attempt else _tr('suivi_raspberry_ui_text_88')
        if not self.config['enabled'] or self.config['away']:
            next_at = _tr('suivi_raspberry_ui_text_92')
        attente = ''
        if self.last_pending is not None:
            if self.last_pending > 0:
                attente = _tr('suivi_raspberry_ui_text_94').format(v0=self.last_pending)
            else:
                attente = _tr('suivi_raspberry_ui_text_96')
        self.detail.set(
            _tr('suivi_raspberry_ui_text_98').format(v0=local_date(state.get('last_contact')), v1=next_at, v2=local_date(state.get('last_attempt')), v3=state.get('last_error') or _tr('suivi_raspberry_ui_text_99'), v4=self.last_result or _tr('suivi_raspberry_ui_text_100'), v5=attente))
        self.buttons = [button for button in self.buttons if button.winfo_exists()]
        for button in self.buttons:
            button.configure(state='disabled' if self.busy else 'normal')

    def card(self, parent, colors):
        card = tk.Frame(parent, bg=colors['CARD'], highlightbackground=colors['BORDER'], highlightthickness=1)
        card.pack(fill='x', padx=20, pady=(0, 12))
        tk.Label(card, text=_tr('suivi_raspberry_ui_text_108'), bg=colors['CARD'], fg=colors['TEXT'], font=('Segoe UI', 13, 'bold')).pack(anchor='w', padx=12, pady=(10, 4))
        tk.Label(card, textvariable=self.title, bg=colors['CARD'], fg=colors['TEXT'], font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=12)
        tk.Label(card, textvariable=self.detail, bg=colors['CARD'], fg=colors['SECONDARY'], justify='left', anchor='w', wraplength=820).pack(fill='x', padx=12, pady=6)
        bar = tk.Frame(card, bg=colors['CARD'])
        bar.pack(fill='x', padx=12, pady=(0, 10))
        for text, command in [(_tr('suivi_raspberry_ui_text_115'), self.check), (_tr('suivi_raspberry_ui_text_115_more'), self.settings)]:
            button = tk.Button(bar, text=text, command=command)
            button.pack(side='left', padx=(0, 8))
            self.buttons.append(button)
        self.render()

    def settings(self):
        if self.busy:
            return
        window = tk.Toplevel(self.root)
        window.title(_tr('suivi_raspberry_ui_text_123'))
        window.transient(self.root)
        window.grab_set()
        config = dict(self.config or {})
        enabled = tk.BooleanVar(window, value=config.get('enabled', False))
        away = tk.BooleanVar(window, value=config.get('away', False))
        tk.Checkbutton(window, text=_tr('suivi_raspberry_ui_text_131'), variable=enabled).pack(anchor='w', padx=16, pady=6)
        tk.Checkbutton(window, text=_tr('suivi_raspberry_ui_text_132'), variable=away).pack(anchor='w', padx=16)
        fields = {}
        for key, label, default in [('hour', _tr('suivi_raspberry_ui_text_134'), '18:00'), ('retry_minutes', _tr('suivi_raspberry_ui_text_134_more'), 15), ('grace_minutes', _tr('suivi_raspberry_ui_text_134_more_more'), 60), ('host', _tr('suivi_raspberry_ui_text_134_more_more_more'), ''), ('user', _tr('suivi_raspberry_ui_text_132_more'), 'botaneo'), ('hostname', _tr('suivi_raspberry_ui_text_134_more_more_more_more'), 'botaneo-pi'), ('key', _tr('suivi_raspberry_ui_text_134_more_more_more_more_more'), '')]:
            tk.Label(window, text=label).pack(anchor='w', padx=16, pady=(6, 0))
            value = tk.StringVar(window, value=str(config.get(key, default)))
            tk.Entry(window, textvariable=value, width=65).pack(fill='x', padx=16)
            fields[key] = value
        tk.Label(window, text=_tr('suivi_raspberry_ui_text_139'), justify='left').pack(padx=16, pady=10)
        def save():
            if self.busy:
                messagebox.showinfo(_tr('suivi_raspberry_ui_text_123'), _tr('suivi_raspberry_ui_text_142'), parent=window)
                return
            try:
                updated = dict(config)
                updated.update({key: value.get().strip() for key, value in fields.items()})
                updated.update(enabled=enabled.get(), away=away.get())
                for key in ('retry_minutes', 'grace_minutes'):
                    updated[key] = int(updated[key])
                save_config(self.path, updated)
                if any(updated.get(key) != config.get(key) for key in ('host', 'user', 'hostname', 'key', 'hour')):
                    self.store.reset()
                self.next_attempt = None
                self.config = updated
                self.config_error = None
                self.runtime_error = None
                window.destroy()
                self.render()
            except (ValueError, OSError):
                messagebox.showerror(_tr('suivi_raspberry_ui_text_123'), _tr('suivi_raspberry_ui_text_160'), parent=window)
        tk.Button(window, text=_tr('save'), command=save).pack(pady=(0, 12))

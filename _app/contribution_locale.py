"""Préparation locale facultative. Aucun transport réseau ; démo exclue."""
import json
import os
import re
import secrets
from pathlib import Path
from botaneo_config import CONFIG_DIR, ecrire_json, lire_json
from i18n import traduire_courant as t


def mode_demo():
    return os.environ.get('BOTANEO_DEMO') == '1'


def chemin():
    return CONFIG_DIR / 'contribution.local.json'


def lire_etat():
    return lire_json(chemin()) if chemin().exists() else {}


def valider_identite(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError(t('contribution_invalid_key'))
    if not all(isinstance(data.get(k), str) and re.fullmatch(r'[A-Za-z0-9_-]{43}', data[k])
               for k in ('contributor_id', 'management_key')):
        raise ValueError(t('contribution_invalid_key'))
    return {k: data[k] for k in ('schema_version', 'contributor_id', 'management_key')}


def preparer_identite():
    if mode_demo():
        raise ValueError(t('contribution_demo_blocked'))
    state = lire_etat()
    if 'contributor_id' in state or 'management_key' in state:
        return valider_identite(state)
    identity = {'schema_version': 1, 'contributor_id': secrets.token_urlsafe(32),
                'management_key': secrets.token_urlsafe(32)}
    state.update(identity)
    state['sharing_enabled'] = False
    chemin().parent.mkdir(parents=True, exist_ok=True)
    ecrire_json(chemin(), state)
    return identity


def marquer_information_lue():
    if mode_demo():
        return
    state = lire_etat()
    state['information_seen'] = True
    state['sharing_enabled'] = False
    chemin().parent.mkdir(parents=True, exist_ok=True)
    ecrire_json(chemin(), state)


def ouvrir_information(parent):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    window = tk.Toplevel(parent)
    window.title(t('contribution_title'))
    window.geometry('700x460')
    window.minsize(440, 320)
    footer = ttk.Frame(window, padding=12)
    footer.pack(side='bottom', fill='x')
    area = ttk.Frame(window, padding=12)
    area.pack(fill='both', expand=True)
    text = tk.Text(area, wrap='word', height=12)
    scroll = ttk.Scrollbar(area, command=text.yview)
    text.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    text.pack(fill='both', expand=True)
    text.insert('1.0', t('contribution_explanation'))
    if mode_demo():
        text.insert('end', '\n\n' + t('contribution_demo_blocked'))
    text.configure(state='disabled')
    status = tk.StringVar(value=t('contribution_offline'))
    ttk.Label(footer, textvariable=status, wraplength=650).pack(fill='x', pady=(0,8))

    def backup_key():
        try:
            # Demander la destination avant de créer une identité locale.
            destination = filedialog.asksaveasfilename(parent=window, defaultextension='.json',
                initialfile='gruterra-cle-privee.json', filetypes=[('JSON','*.json')])
            if not destination:
                return
            if Path(destination).exists():
                raise ValueError(t('contribution_no_overwrite'))
            identity = preparer_identite()
            with Path(destination).open('x', encoding='utf-8') as stream:
                json.dump(identity, stream, ensure_ascii=False, indent=2)
            status.set(t('contribution_key_saved'))
        except (OSError, ValueError, RuntimeError) as error:
            messagebox.showerror(t('contribution_title'), str(error), parent=window)

    def restore_key():
        try:
            source = filedialog.askopenfilename(parent=window,filetypes=[('JSON','*.json')])
            if not source:
                return
            identity = valider_identite(lire_json(source))
            state = lire_etat()
            if 'management_key' in state and state['management_key'] != identity['management_key']:
                raise ValueError(t('contribution_existing_key'))
            state.update(identity)
            state['sharing_enabled'] = False
            chemin().parent.mkdir(parents=True, exist_ok=True)
            ecrire_json(chemin(), state)
            status.set(t('contribution_key_restored'))
        except (OSError, ValueError, RuntimeError) as error:
            messagebox.showerror(t('contribution_title'), str(error), parent=window)

    def close():
        try:
            marquer_information_lue()
        except RuntimeError as error:
            messagebox.showerror(t('contribution_title'), str(error), parent=window)
            return
        window.destroy()

    controls = ttk.Frame(footer)
    controls.pack(fill='x')
    if not mode_demo():
        ttk.Button(controls, text=t('contribution_backup_key'), command=backup_key).pack(side='left')
        ttk.Button(controls, text=t('contribution_restore_key'), command=restore_key).pack(side='left', padx=8)
    ttk.Button(controls, text=t('close'), command=close).pack(side='right')
    window.protocol('WM_DELETE_WINDOW', close)
    return window


def proposer_premier_lancement(parent):
    if mode_demo():
        return
    try:
        if not lire_etat().get('information_seen'):
            ouvrir_information(parent)
    except RuntimeError:
        # Un fichier existant illisible ne doit jamais être remplacé automatiquement.
        from tkinter import messagebox
        messagebox.showerror(t('contribution_title'), t('contribution_config_unreadable'), parent=parent)

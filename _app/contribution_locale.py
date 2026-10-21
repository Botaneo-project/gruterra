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



def restaurer_identite(data):
    """Restaure le couple complet sans remplacer une identité ni activer le partage."""
    if mode_demo():
        raise ValueError(t('contribution_demo_blocked'))
    identity = valider_identite(data)
    state = lire_etat()
    if 'contributor_id' in state or 'management_key' in state:
        current = valider_identite(state)
        if current != identity:
            raise ValueError(t('contribution_existing_key'))
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


def ouvrir_information(parent, palette=None):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
    window = tk.Toplevel(parent)
    window.title(t('contribution_title'))
    window.geometry('700x460')
    window.minsize(440, 320)
    from ui_palette import THEME_CLAIR, THEME_SOMBRE
    from ui_scroll_form import create, create_text
    from meteo_nappes import harmoniser
    palette = palette or (THEME_SOMBRE if parent.cget('background') == THEME_SOMBRE['BG'] else THEME_CLAIR)
    body, footer = create(window, palette)
    text = create_text(body, palette, height=10, padx=12, pady=12)
    text.insert('1.0', t('contribution_explanation'))
    if mode_demo():
        text.insert('end', '\n\n' + t('contribution_demo_blocked'))
    text.configure(state='disabled')
    status = tk.StringVar(value=t('contribution_offline'))
    tk.Label(body, textvariable=status, wraplength=380, justify='left').pack(fill='x', padx=12, pady=8)

    def backup_key():
        try:
            # Demander la destination avant de créer une identité locale.
            destination = filedialog.asksaveasfilename(parent=window, defaultextension='.json',
                initialfile='gruterra-cle-privee.json', filetypes=[('JSON','*.json')])
            if not destination:
                return
            if Path(destination).exists():
                raise ValueError(t('contribution_no_overwrite'))
            from contribution_identite import sauvegarder
            passphrase = simpledialog.askstring(t('contribution_title'), t('contribution_password_prompt'), show='*', parent=window)
            if passphrase is None:
                return
            confirmation = simpledialog.askstring(t('contribution_title'), t('contribution_password_confirm'), show='*', parent=window)
            if confirmation is None:
                return
            if passphrase != confirmation:
                raise ValueError(t('contribution_password_mismatch'))
            sauvegarder(destination, passphrase)
            status.set(t('contribution_key_saved'))
        except (OSError, ValueError, RuntimeError) as error:
            messagebox.showerror(t('contribution_title'), str(error), parent=window)

    def restore_key():
        try:
            source = filedialog.askopenfilename(parent=window,filetypes=[('JSON','*.json')])
            if not source:
                return
            data = lire_json(source)
            if data.get('identity_version') == 2:
                from contribution_identite import restaurer_sauvegarde
                passphrase = simpledialog.askstring(t('contribution_title'), t('contribution_password_restore'), show='*', parent=window)
                if passphrase is None:
                    return
                restaurer_sauvegarde(data, passphrase)
            else:
                restaurer_identite(data)
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

    controls = tk.Frame(body)
    controls.pack(fill='x', padx=12, pady=8)
    if not mode_demo():
        tk.Button(controls, text=t('contribution_backup_key'), command=backup_key).pack(fill='x', pady=3)
        tk.Button(controls, text=t('contribution_restore_key'), command=restore_key).pack(fill='x', pady=3)
        from contribution_suivi import ouvrir_suivi
        tk.Button(controls, text=t('contribution_tracking_title'), command=lambda: ouvrir_suivi(window, palette)).pack(fill='x', pady=3)
    tk.Button(footer, text=t('close'), command=close).pack(side='right')
    def resize_controls(event):
        for child in controls.winfo_children():
            child.configure(wraplength=max(160,event.width-24))
    controls.bind('<Configure>', resize_controls)
    harmoniser(window, palette)
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

"""Editable observations after watering; never changes watering time or volume."""
from contextlib import closing
from datetime import datetime
import math
import database

CHOICES=('unknown','none','light','clear','not_checked')


def initialize(db):
    db.execute('''CREATE TABLE IF NOT EXISTS watering_observations_v1 (
        watering_id INTEGER PRIMARY KEY REFERENCES arrosages(id),
        drainage TEXT NOT NULL, first_drops_minutes REAL,
        observed_at TEXT NOT NULL, updated_at TEXT NOT NULL)''')


def load(watering_id):
    with closing(database.get_connection()) as db:
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE name='watering_observations_v1'").fetchone()
        if not exists:return None
        row=db.execute('SELECT drainage,first_drops_minutes,observed_at,updated_at FROM watering_observations_v1 WHERE watering_id=?',(watering_id,)).fetchone()
    return dict(zip(('drainage','first_drops_minutes','observed_at','updated_at'),row)) if row else None


def save(plant_id,watering_id,drainage='unknown',minutes=None):
    if drainage not in CHOICES:raise ValueError('Invalid drainage observation')
    if minutes is not None:
        if isinstance(minutes,bool) or not isinstance(minutes,(int,float)) or not math.isfinite(minutes) or minutes<0:
            raise ValueError('Invalid first-drops time')
        if drainage not in ('light','clear'):raise ValueError('First drops require observed drainage')
    now=datetime.now().isoformat(timespec='seconds')
    with closing(database.get_connection()) as db:
        with db:
            if not db.execute('SELECT 1 FROM arrosages WHERE id=? AND plante_id=?',(watering_id,plant_id)).fetchone():
                raise ValueError('Unknown watering for this plant')
            initialize(db)
            db.execute('''INSERT INTO watering_observations_v1 VALUES (?,?,?,?,?)
                ON CONFLICT(watering_id) DO UPDATE SET drainage=excluded.drainage,
                first_drops_minutes=excluded.first_drops_minutes, updated_at=excluded.updated_at''',
                (watering_id,drainage,minutes,now,now))


def open_editor(parent,plant_id,palette,on_saved=None):
    import tkinter as tk
    from tkinter import ttk,messagebox
    from i18n import traduire_courant as t
    from ui_scroll_form import create
    rows=database.get_arrosages_plante(plant_id,limite=200)
    window=tk.Toplevel(parent);window.title(t('watering_observation_edit'))
    window.geometry('560x410');window.minsize(400,280);window.configure(bg=palette['BG'])
    body,footer=create(window,palette)
    if not rows:
        tk.Label(body,text=t('watering_observation_empty'),bg=palette['BG'],fg=palette['TEXT']).pack(padx=16,pady=16)
        ttk.Button(footer,text=t('lighting_close'),command=window.destroy).pack()
        return window
    labels=[str(row[2])+' · '+str(row[3])+' ml · #'+str(row[0]) for row in rows]
    selected=tk.StringVar(window,value=labels[0])
    ttk.Combobox(body,textvariable=selected,values=labels,state='readonly').pack(fill='x',padx=16,pady=12)
    tk.Label(body,text=t('watering_observation_help'),wraplength=480,justify='left',bg=palette['BG'],fg=palette['TEXT']).pack(fill='x',padx=16)
    choice_keys=('not_specified','drainage_none','drainage_light','drainage_clear','not_checked')
    choices=[t(k) for k in choice_keys];drainage=tk.StringVar(window,value=choices[0])
    ttk.Combobox(body,textvariable=drainage,values=choices,state='readonly').pack(fill='x',padx=16,pady=10)
    tk.Label(body,text=t('drainage_delay'),bg=palette['BG'],fg=palette['TEXT']).pack(anchor='w',padx=16)
    minutes=tk.StringVar(window)
    ttk.Entry(body,textvariable=minutes).pack(fill='x',padx=16,pady=6)
    feedback=tk.StringVar(window)
    tk.Label(body,textvariable=feedback,wraplength=480,bg=palette['BG'],fg=palette['SECONDARY']).pack(fill='x',padx=16,pady=8)
    def refresh(event=None):
        value=load(rows[labels.index(selected.get())][0]) or {}
        code=value.get('drainage','unknown')
        drainage.set(choices[CHOICES.index(code)] if code in CHOICES else choices[0])
        minutes.set('' if value.get('first_drops_minutes') is None else str(value['first_drops_minutes']))
        feedback.set('')
    def persist():
        try:
            value=minutes.get().strip().replace(',','.')
            save(plant_id,rows[labels.index(selected.get())][0],CHOICES[choices.index(drainage.get())],float(value) if value else None)
        except (ValueError,OSError, __import__('sqlite3').Error):
            feedback.set(t('watering_observation_invalid'));return
        feedback.set(t('watering_observation_saved'))
        if on_saved:on_saved()
    # Bind the watering selector only; changing drainage must not reload old input.
    next(w for w in body.winfo_children() if isinstance(w,ttk.Combobox)).bind('<<ComboboxSelected>>',refresh)
    ttk.Button(footer,text=t('save'),command=persist).pack(side='right',padx=8,pady=8)
    ttk.Button(footer,text=t('lighting_close'),command=window.destroy).pack(side='right',padx=8,pady=8)
    from meteo_nappes import harmoniser
    def style(w):
        if isinstance(w,(ttk.Combobox,ttk.Treeview)):harmoniser(w,palette)
        for child in w.winfo_children():style(child)
    style(body);refresh()
    return window

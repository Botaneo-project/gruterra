"""Responsive lighting-window history, without changing measurement data."""
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import database
from ui_palette import readable_text
from botaneo_dates import vers_local_naif
from i18n import traduire_courant as t
from light_schedule import load, save, analyse, validate, analyse_profile

from botaneo_config import CONFIG_DIR
CONFIG = CONFIG_DIR/'light-schedules.json'


def graph_layout(group, start, end, width, height):
    """Use the entire configured window, without smoothing or extrapolation."""
    validate(start, end)
    begin = datetime.fromisoformat(group['day']+'T'+start)
    stop = datetime.fromisoformat(group['day']+'T'+end)
    if stop <= begin:
        stop += timedelta(days=1)
    left, right, top, bottom = 65, max(100, width-20), 25, max(70, height-40)
    maximum = max(1, group['maximum']*1.12)
    span = (stop-begin).total_seconds()
    points = []
    for row in group['points']:
        at = vers_local_naif(row['at'])
        if at is not None and begin <= at < stop:
            points.append({'at': at, 'lux': row['lux'], 'source': row['at'],
                           'x': left+(at-begin).total_seconds()/span*(right-left),
                           'y': bottom-row['lux']/maximum*(bottom-top)})
    return {'points': sorted(points, key=lambda row: row['at']), 'begin': begin, 'end': stop,
            'maximum': maximum, 'left': left, 'right': right, 'top': top, 'bottom': bottom}


def observation_summary(group, start, end, now=None):
    layout = graph_layout(group, start, end, 600, 235)
    points = layout['points']
    if not points:
        return None
    current = vers_local_naif(now) if now is not None else datetime.now()
    phase = 'before' if current < layout['begin'] else 'ongoing' if current < layout['end'] else 'ended'
    gaps = [(right['at']-left['at']).total_seconds() for left, right in zip(points, points[1:])]
    return {'first': points[0]['at'], 'last': points[-1]['at'],
            'largest_gap_seconds': max(gaps) if gaps else None, 'phase': phase}


def open_window(parent, plant_id, palette=None):
    from vue_historique import theme_actuel
    colors = {**theme_actuel(), **(palette or {})}
    win = tk.Toplevel(parent)
    win.title(t('lighting_title'))
    win.geometry('1020x800')
    win.minsize(620, 460)
    win.configure(bg=colors['BG'])
    settings = load(CONFIG, plant_id) or {'start': '09:50', 'end': '15:50'}
    start, end = tk.StringVar(value=settings['start']), tk.StringVar(value=settings['end'])
    groups, plotted, selected_point = [], [], [None]
    displayed_schedule = dict(settings)
    notice = tk.StringVar()
    style = ttk.Style(win)
    prefix = 'Lighting'+str(id(win))
    style.configure(prefix+'.Treeview', background=colors['CARD'], fieldbackground=colors['CARD'], foreground=colors['TEXT'], rowheight=27)
    style.configure(prefix+'.Treeview.Heading', background=colors['BG'], foreground=colors['TEXT'])
    style.map(prefix+'.Treeview', background=[('selected', colors['BLUE'])], foreground=[('selected', colors['CARD'])])
    style.configure(prefix+'.TCombobox', fieldbackground=colors['CARD'], foreground=colors['TEXT'])
    style.map(prefix+'.TCombobox', fieldbackground=[('readonly', colors['CARD'])], foreground=[('readonly', colors['TEXT'])])
    def frame(master, **kwargs):
        return tk.Frame(master, bg=colors['BG'], **kwargs)
    def label(master, **kwargs):
        kwargs.setdefault('fg', colors['TEXT'])
        kwargs.setdefault('bg', colors['BG'])
        return tk.Label(master, **kwargs)
    def button(master, text, command, **kwargs):
        primary = text == t('lighting_save')
        background = colors['GREEN'] if primary else colors['CARD']
        foreground = readable_text(background) if primary else colors['TEXT']
        return tk.Button(master, text=text, command=command, bg=background, fg=foreground, activebackground=colors['LIGHT_GREEN'], activeforeground=colors['TEXT'], relief='flat', padx=12, pady=7, **kwargs)
    footer = frame(win)
    footer.pack(side='bottom', fill='x', padx=16, pady=10)
    button(footer, t('lighting_close'), win.destroy).pack(side='right')
    copy_button = button(footer, t('lighting_copy_day'), lambda:copy_day())
    copy_button.pack(side='left')
    button(footer, t('lighting_refresh'), lambda:refresh()).pack(side='left', padx=8)
    outer = frame(win)
    outer.pack(fill='both', expand=True)
    scroll_canvas = tk.Canvas(outer, bg=colors['BG'], highlightthickness=0)
    vertical = ttk.Scrollbar(outer, orient='vertical', command=scroll_canvas.yview)
    vertical.pack(side='right', fill='y')
    scroll_canvas.pack(side='left', fill='both', expand=True)
    scroll_canvas.configure(yscrollcommand=vertical.set)
    body = frame(scroll_canvas)
    body_id = scroll_canvas.create_window(0, 0, window=body, anchor='nw')
    body.bind('<Configure>', lambda event:scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
    def resize_body(event):
        scroll_canvas.itemconfigure(body_id, width=event.width)
        for widget in wrapping:
            widget.configure(wraplength=max(260, event.width-55))
    scroll_canvas.bind('<Configure>', resize_body)
    wrapping = []
    label(body, text=t('lighting_title'), font=('Segoe UI', 19, 'bold'), anchor='w').pack(fill='x', padx=20, pady=(16, 5))
    subtitle = label(body, text=t('lighting_ui_subtitle'), justify='left', anchor='w', fg=colors['SECONDARY'])
    subtitle.pack(fill='x', padx=20, pady=(0, 14))
    wrapping.append(subtitle)
    controls = frame(body, highlightbackground=colors['BORDER'], highlightthickness=1)
    controls.pack(fill='x', padx=20, pady=4)
    for column in range(4):
        controls.columnconfigure(column, weight=1)
    for index, (key, variable) in enumerate((('lighting_on', start), ('lighting_off', end))):
        label(controls, text=t(key), anchor='w').grid(row=0, column=index*2, sticky='w', padx=12, pady=10)
        entry = tk.Entry(controls, textvariable=variable, width=7, bg=colors['CARD'], fg=colors['TEXT'], insertbackground=colors['TEXT'], font=('Segoe UI', 11))
        entry.grid(row=0, column=index*2+1, sticky='w', padx=8)
    button(controls, t('lighting_save'), lambda:refresh(True)).grid(row=1, column=0, columnspan=2, sticky='w', padx=12, pady=(0, 10))
    button(controls, t('lighting_sync'), lambda:sync_now()).grid(row=1, column=2, columnspan=2, sticky='e', padx=12, pady=(0, 10))
    notice_label = label(body, textvariable=notice, anchor='w', justify='left', fg=colors['BLUE'])
    notice_label.pack(fill='x', padx=20, pady=8)
    wrapping.append(notice_label)
    selection = frame(body)
    selection.pack(fill='x', padx=20, pady=8)
    selection.columnconfigure(2, weight=1)
    label(selection, text=t('lighting_ui_day_select')).grid(row=0, column=0, sticky='w', padx=(0, 8))
    previous_button = button(selection, t('lighting_ui_previous'), lambda:navigate(1))
    previous_button.grid(row=0, column=1, padx=4)
    day = ttk.Combobox(selection, state='readonly', width=20, style=prefix+'.TCombobox')
    day.grid(row=0, column=2, sticky='ew', padx=4)
    next_button = button(selection, t('lighting_ui_next'), lambda:navigate(-1))
    next_button.grid(row=0, column=3, padx=4)
    count_label = tk.StringVar()
    label(selection, textvariable=count_label, fg=colors['SECONDARY']).grid(row=1, column=0, columnspan=4, sticky='w', pady=(5,0))
    cards = frame(body)
    cards.pack(fill='x', padx=20, pady=(0, 12))
    values = {}
    for index, (key, title) in enumerate((('count', 'lighting_count'), ('mean', 'lighting_mean'), ('minimum', 'lighting_min'), ('maximum', 'lighting_max'))):
        card = tk.Frame(cards, bg=colors['CARD'], highlightbackground=colors['BORDER'], highlightthickness=1)
        card.grid(row=0, column=index, sticky='nsew', padx=(0, 8 if index < 3 else 0))
        cards.columnconfigure(index, weight=1)
        values[key] = tk.StringVar(value='—')
        label(card, text=t(title), bg=colors['CARD'], fg=colors['SECONDARY'], font=('Segoe UI', 10)).pack(padx=8, pady=(10, 2))
        label(card, textvariable=values[key], bg=colors['CARD'], fg=colors['BLUE'], font=('Segoe UI', 17, 'bold')).pack(padx=8, pady=(0, 10))
    observation_note = tk.StringVar()
    observation_label = label(body, textvariable=observation_note, anchor='w', justify='left', fg=colors['SECONDARY'])
    observation_label.pack(fill='x', padx=20, pady=(0, 10))
    wrapping.append(observation_label)
    tab_bar = frame(body)
    tab_bar.pack(fill='x', padx=20, pady=(8, 0))
    tab_bar.columnconfigure(0, weight=1)
    tab_bar.columnconfigure(1, weight=1)
    panel = frame(body)
    panel.pack(fill='both', expand=True, padx=20, pady=(0, 8))
    detail = frame(panel)
    comparison = frame(panel)
    tab_buttons = {}
    def show_panel(name):
        detail.pack_forget()
        comparison.pack_forget()
        (detail if name == 'detail' else comparison).pack(fill='both', expand=True)
        for key, item in tab_buttons.items():
            selected = key == name
            background = colors['GREEN'] if selected else colors['CARD']
            item.configure(bg=background, fg=readable_text(background) if selected else colors['TEXT'],
                           relief='sunken' if selected else 'flat', borderwidth=1)
    for index, (name, key) in enumerate((('detail', 'lighting_ui_detail_tab'), ('comparison', 'lighting_ui_compare_tab'))):
        item = tk.Button(tab_bar, text=t(key), command=lambda name=name:show_panel(name),
                         font=('Segoe UI', 11, 'bold'), wraplength=240, padx=10, pady=12,
                         activebackground=colors['LIGHT_GREEN'], activeforeground=colors['TEXT'],
                         highlightthickness=1, highlightbackground=colors['BORDER'], takefocus=True)
        item.grid(row=0, column=index, sticky='nsew', padx=(0, 6) if index == 0 else (6, 0))
        tab_buttons[name] = item
    show_panel('detail')
    help_label = label(detail, text=t('lighting_ui_graph_help'), anchor='w', justify='left', fg=colors['SECONDARY'])
    help_label.pack(fill='x', pady=8)
    wrapping.append(help_label)
    graph = tk.Canvas(detail, height=235, bg=colors['CARD'], highlightthickness=0)
    graph.pack(fill='x')
    selected_label = tk.StringVar(value=t('lighting_ui_no_selection'))
    label(detail, textvariable=selected_label, anchor='w', fg=colors['BLUE']).pack(fill='x', pady=6)
    def table(master, columns, headings, height):
        holder = frame(master)
        holder.pack(fill='both', expand=True, pady=6)
        holder.columnconfigure(0, weight=1)
        holder.rowconfigure(0, weight=1)
        tree = ttk.Treeview(holder, columns=columns, show='headings', height=height, style=prefix+'.Treeview')
        for column, heading in zip(columns, headings):
            tree.heading(column, text=t(heading))
            tree.column(column, width=170, minwidth=100, anchor='center')
        tree.grid(row=0, column=0, sticky='nsew')
        v = ttk.Scrollbar(holder, orient='vertical', command=tree.yview)
        v.grid(row=0, column=1, sticky='ns')
        h = ttk.Scrollbar(holder, orient='horizontal', command=tree.xview)
        h.grid(row=1, column=0, sticky='ew')
        tree.configure(yscrollcommand=v.set, xscrollcommand=h.set)
        return tree
    readings = table(detail, ('at', 'lux'), ('lighting_ui_at', 'lighting_ui_lux'), 5)
    days = table(comparison, ('day', 'count', 'mean', 'minimum', 'maximum'), ('lighting_day', 'lighting_count', 'lighting_mean', 'lighting_min', 'lighting_max'), 10)
    footnote = label(body, text=t('lighting_note'), anchor='w', justify='left', fg=colors['SECONDARY'])
    footnote.pack(fill='x', padx=20, pady=(8, 16))
    wrapping.append(footnote)
    def current_group():
        index = day.current()
        return groups[index] if 0 <= index < len(groups) else None
    def point_label(row):
        selected_label.set(t('lighting_ui_selected_point').format(time=row['at'].strftime('%d/%m/%Y %H:%M:%S'), value=f"{row['lux']:g}"))
    def draw(event=None):
        nonlocal plotted
        graph.delete('all')
        group = current_group()
        plotted = []
        if not group:
            graph.create_text(max(120, graph.winfo_width()/2), 100, text=t('lighting_ui_empty'), fill=colors['SECONDARY'], width=max(200, graph.winfo_width()-40))
            return
        layout = graph_layout(group, group.get('start',displayed_schedule['start']), group.get('end',displayed_schedule['end']), graph.winfo_width(), graph.winfo_height())
        plotted = layout['points']
        left, right, top, bottom = (layout[key] for key in ('left', 'right', 'top', 'bottom'))
        for index in range(5):
            y = bottom-index*(bottom-top)/4
            graph.create_line(left, y, right, y, fill=colors['BORDER'])
            graph.create_text(left-9, y, text=f"{layout['maximum']*index/4:.0f}", anchor='e', fill=colors['SECONDARY'])
            at = layout['begin']+(layout['end']-layout['begin'])*index/4
            x = left+(right-left)*index/4
            graph.create_text(x, bottom+18, text=at.strftime('%H:%M'), fill=colors['SECONDARY'])
        graph.create_text(8, 8, text='lux', anchor='nw', fill=colors['SECONDARY'])
        previous = None
        for index, row in enumerate(plotted):
            if previous and (row['at']-previous['at']).total_seconds() <= 5400:
                graph.create_line(previous['x'], previous['y'], row['x'], row['y'], fill=colors['BLUE'], width=2)
            graph.create_oval(row['x']-3, row['y']-3, row['x']+3, row['y']+3, fill=colors['BLUE'], outline=colors['BLUE'])
            if selected_point[0] == index:
                graph.create_line(row['x'], top, row['x'], bottom, fill=colors['ORANGE'], dash=(3, 4))
                graph.create_oval(row['x']-5, row['y']-5, row['x']+5, row['y']+5, fill=colors['ORANGE'], outline=colors['CARD'])
            previous = row
    def select_point(event=None):
        selection = readings.selection()
        if selection and int(selection[0]) < len(plotted):
            selected_point[0] = int(selection[0])
            point_label(plotted[selected_point[0]])
            draw()
    def click_graph(event):
        if plotted:
            index = min(range(len(plotted)), key=lambda i:abs(plotted[i]['x']-event.x))
            readings.selection_set(str(index))
            readings.see(str(index))
    def show_day(event=None):
        group = current_group()
        readings.delete(*readings.get_children())
        selected_point[0] = None
        previous_button.configure(state='normal' if day.current()+1 < len(groups) and day.current() >= 0 else 'disabled')
        next_button.configure(state='normal' if day.current() > 0 else 'disabled')
        if not group:
            observation_note.set(t('lighting_ui_empty'))
            for variable in values.values():
                variable.set('—')
            copy_button.configure(state='disabled')
            selected_label.set(t('lighting_ui_no_selection'))
            draw()
            return
        copy_button.configure(state='normal')
        index = str(day.current())
        if days.selection() != (index,):
            days.selection_set(index)
            days.see(index)
        observed = observation_summary(group, group.get('start',displayed_schedule['start']), group.get('end',displayed_schedule['end']))
        if observed:
            span = t('lighting_ui_observed_span').format(first=observed['first'].strftime('%d/%m %H:%M'), last=observed['last'].strftime('%d/%m %H:%M'))
            gap = t('lighting_ui_single_sample') if observed['largest_gap_seconds'] is None else t('lighting_ui_largest_gap').format(minutes=f"{observed['largest_gap_seconds']/60:.0f}")
            observation_note.set(span+'\n'+gap+'\n'+t('lighting_ui_phase_'+observed['phase']))
        for key in values:
            values[key].set(str(group[key]) if key == 'count' else f'{group[key]:g} lux')
        draw()
        for index, row in enumerate(plotted):
            readings.insert('', 'end', iid=str(index), values=(row['at'].strftime('%d/%m/%Y %H:%M:%S'), f"{row['lux']:g}"))
        if plotted:
            readings.selection_set(str(len(plotted)-1))
            readings.see(str(len(plotted)-1))
            select_point()
    def compare_select(event=None):
        selected = days.selection()
        if selected and day.current() != int(selected[0]):
            day.current(int(selected[0]))
            show_day()
    def navigate(offset):
        index = day.current()+offset
        if 0 <= index < len(groups):
            day.current(index)
            show_day()
    def copy_day():
        group = current_group()
        if not group:
            return
        rows = [t('lighting_title'), t('lighting_ui_copy_window').format(day=group['day'], start=group.get('start',displayed_schedule['start']), end=group.get('end',displayed_schedule['end'])), t('lighting_header').rstrip()]
        rows += [row['at'].strftime('%d/%m/%Y %H:%M:%S')+'\t'+f"{row['lux']:g}" for row in plotted]
        win.clipboard_clear()
        win.clipboard_append('\n'.join(rows))
        notice.set(t('lighting_ui_copied').format(count=len(plotted)))
    def refresh(persist=False):
        nonlocal groups
        selected_day = current_group()['day'] if current_group() else None
        try:
            validate(start.get(), end.get())
            if persist:
                save(CONFIG, plant_id, start.get(), end.get())
            conn = database.get_connection()
            try:
                raw = conn.execute('SELECT m.date_heure,m.luminosite FROM mesures m JOIN capteurs c ON c.id=m.capteur_id WHERE c.plante_id=? AND m.date_heure>=? ORDER BY m.date_heure', (plant_id, (datetime.now()-timedelta(days=30)).date().isoformat())).fetchall()
            finally:
                conn.close()
            stored=load(CONFIG, plant_id)
            selected=stored if stored and stored['start']==start.get() and stored['end']==end.get() else validate(start.get(),end.get())
            groups = analyse_profile([{'at': row[0], 'lux': row[1]} for row in raw], selected)
            first_day = (datetime.now()-timedelta(days=29)).date().isoformat()
            last_day = datetime.now().date().isoformat()
            groups = [group for group in groups if first_day <= group['day'] <= last_day]
            displayed_schedule.update(start=start.get(), end=end.get())
            day.configure(values=[datetime.fromisoformat(group['day']).strftime('%d/%m/%Y') for group in groups])
            days.delete(*days.get_children())
            for index, group in enumerate(groups):
                days.insert('', 'end', iid=str(index), values=(datetime.fromisoformat(group['day']).strftime('%d/%m/%Y'), group['count'], f"{group['mean']:.1f}", f"{group['minimum']:g}", f"{group['maximum']:g}"))
            count_label.set(t('lighting_ui_days_count').format(count=len(groups)))
            if groups:
                index = next((i for i, group in enumerate(groups) if group['day'] == selected_day), 0)
                day.current(index)
                days.selection_set(str(index))
            else:
                day.set('')
            summary = t('lighting_ui_summary').format(count=len(groups), start=displayed_schedule['start'], end=displayed_schedule['end'])
            saved = load(CONFIG, plant_id) or {'start': '09:50', 'end': '15:50'}
            if saved is None or validate(saved['start'],saved['end']) != validate(displayed_schedule['start'],displayed_schedule['end']):
                summary += ' '+t('lighting_ui_not_saved')
            notice.set((t('lighting_saved') if persist else '')+summary)
            show_day()
        except ValueError:
            notice.set(t('lighting_invalid'))
        except Exception:
            notice.set(t('lighting_error'))
    def sync_now():
        from lamp_sync import resolve_window
        resolve_window(win, plant_id)
        current = load(CONFIG, plant_id)
        if current:
            start.set(current['start'])
            end.set(current['end'])
        refresh()
    def wheel(event):
        if isinstance(event.widget, (ttk.Treeview, ttk.Combobox)):
            return
        scroll_canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
    win.bind('<MouseWheel>', wheel, add='+')
    day.bind('<<ComboboxSelected>>', show_day)
    days.bind('<<TreeviewSelect>>', compare_select)
    readings.bind('<<TreeviewSelect>>', select_point)
    graph.bind('<Configure>', draw)
    graph.bind('<Button-1>', click_graph)
    refresh()
    start.trace_add('write', lambda *args:notice.set(t('lighting_ui_unsaved')))
    end.trace_add('write', lambda *args:notice.set(t('lighting_ui_unsaved')))
    return win

"""Connected sensor dashboard: separate history, explicit manual catch-up."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path


def open_window(parent,palette,*,plant_id=None,config=None,archive_path=None):
    import os
    import tkinter as tk
    from tkinter import ttk,messagebox
    import threading
    from queue import Queue
    from botaneo_config import DATA_DIR
    from home_assistant_ui import load
    from home_assistant_view import read_rows
    from home_assistant_catchup import plan_catchup,run_catchup
    from home_assistant_archive import checkpoint
    from home_assistant_test_ui import open_window as manage_tests
    from i18n import traduire_courant as t
    from meteo_nappes import harmoniser
    from ui_scroll_form import create
    from ui_data_events import notifier_donnees_modifiees
    window=tk.Toplevel(parent)
    window.title(t('ha_view_title'))
    window.geometry('980x680');window.minsize(560,440)
    body,footer=create(window,palette);footer.columnconfigure(0,weight=1)
    demo=os.environ.get('BOTANEO_DEMO')=='1'
    archive=Path(archive_path) if archive_path is not None else Path(DATA_DIR)/'home_assistant_history.sqlite3'
    try:
        cfg={} if demo else (config if config is not None else load())
    except Exception:
        cfg={}
    mappings=[r for r in cfg.get('entities',[]) if plant_id is None or r.get('plant_id')==plant_id]
    current={'rows':[],'busy':False}
    from sensor_conversion_notes import load_notes,relevant_notes
    conversion_notes=[] if demo else load_notes()
    note=tk.Label(body,text=t('ha_view_note'),wraplength=800,justify='left')
    note.pack(fill='x',padx=14,pady=10)
    note.bind('<Configure>',lambda e:note.configure(wraplength=max(160,e.width-12)))
    toolbar=tk.Frame(body);toolbar.pack(fill='x',padx=14)
    metrics=('soil_moisture','air_humidity','temperature','illuminance')
    metric_labels=[t('ha_metric_'+key) for key in metrics]
    selected_metric=tk.StringVar(value=metric_labels[0])
    metric=tk.OptionMenu(toolbar,selected_metric,*metric_labels,command=lambda value:reload())
    metric.pack(anchor='w')
    from sensor_source_policy import hardware_id
    devices={}
    device_mappings=mappings
    if demo:
        device_mappings=[{'hardware_id':'zigbee:0011223344556677','model':'ZS-304Z'}]
    for mapping in device_mappings:
        try:
            physical=hardware_id(mapping.get('hardware_id'))
            devices.setdefault(physical,str(mapping.get('model',''))+' · …'+physical[-4:])
        except ValueError:
            continue
    from collections import Counter
    label_counts=Counter(devices.values())
    devices={physical:(label+' · '+physical if label_counts[label]>1 else label) for physical,label in devices.items()}
    device_ids=[None]+list(devices)
    device_labels=[t('ha_view_all_devices')]+list(devices.values())
    tk.Label(toolbar,text=t('ha_view_device_filter')).pack(anchor='w',pady=(4,0))
    selected_device=tk.StringVar(value=device_labels[0])
    device_selector=tk.OptionMenu(toolbar,selected_device,*device_labels,command=lambda value:reload())
    device_selector.pack(anchor='w')
    from home_assistant_view import plants
    try:
        plant_names={} if demo else dict(plants())
    except Exception:
        plant_names={}
    all_plants=object()
    associated=[]
    for mapping in mappings:
        pid=mapping.get('plant_id')
        if (pid is None or type(pid) is int) and pid not in associated:
            associated.append(pid)
    plant_ids=[plant_id] if plant_id is not None else [all_plants]+associated
    plant_labels=[t('ha_view_all_plants') if pid is all_plants else t('ha_view_unassigned') if pid is None
                  else str(pid)+' — '+plant_names.get(pid,t('ha_association_missing').format(id=pid)) for pid in plant_ids]
    tk.Label(toolbar,text=t('ha_view_plant_filter')).pack(anchor='w',pady=(4,0))
    plant_selector=ttk.Combobox(toolbar,state='disabled' if plant_id is not None else 'readonly',values=plant_labels,width=35)
    plant_selector.current(0);plant_selector.pack(anchor='w')
    def plant_mappings():
        chosen=plant_ids[plant_selector.current()]
        return [row for row in mappings if chosen is all_plants or row.get('plant_id')==chosen]
    def change_plant(event=None,reload_view=True):
        previous=device_ids[device_labels.index(selected_device.get())]
        allowed_devices=set()
        for row in plant_mappings():
            try:allowed_devices.add(hardware_id(row.get('hardware_id')))
            except ValueError:continue
        available={key:label for key,label in devices.items() if key in allowed_devices or demo}
        device_ids[:]=[None]+list(available)
        device_labels[:]=[t('ha_view_all_devices')]+list(available.values())
        menu=device_selector['menu'];menu.delete(0,'end')
        for label in device_labels:
            menu.add_command(label=label,command=tk._setit(selected_device,label,lambda value:reload()))
        selected_device.set(device_labels[device_ids.index(previous)] if previous in device_ids else device_labels[0])
        if reload_view:reload()
    plant_selector.bind('<<ComboboxSelected>>',change_plant)
    raw_states=tk.BooleanVar(value=False)
    tk.Checkbutton(toolbar,text=t('ha_chart_raw_states'),variable=raw_states,command=lambda:draw()).pack(anchor='w',pady=4)
    full_scale=tk.BooleanVar(value=False)
    tk.Checkbutton(toolbar,text=t('ha_chart_full_scale'),variable=full_scale,
                   command=lambda:draw()).pack(anchor='w',pady=4)
    status=tk.StringVar()
    tk.Label(body,textvariable=status,wraplength=760,justify='left').pack(fill='x',padx=14,pady=8)
    conversion_note=tk.Label(body,text='',wraplength=760,justify='left',anchor='w')
    conversion_note.pack(fill='x',padx=14,pady=4)
    canvas=tk.Canvas(body,height=340,background=palette['CARD'],highlightthickness=0)
    canvas.pack(fill='x',padx=14,pady=8)
    tk.Label(body,text=t('ha_chart_help'),wraplength=760,justify='left').pack(fill='x',padx=14,pady=(0,8))
    frame=tk.Frame(body);frame.pack(fill='both',expand=True,padx=14,pady=8)
    frame.columnconfigure(0,weight=1);frame.rowconfigure(0,weight=1)
    names=('date','retrieved','device','metric','value','unit','availability','freshness','kind')
    table=ttk.Treeview(frame,columns=names,show='headings',height=8)
    for key,label in zip(names,('ha_timing_state_date','ha_timing_retrieved','ha_hardware','ha_metric','ha_preview_value','ha_preview_unit','ha_preview_state','ha_preview_freshness','ha_view_kind')):
        table.heading(key,text=t(label));table.column(key,width=160,minwidth=100)
    table.column('value',width=80,minwidth=65,stretch=False)
    table.column('unit',width=60,minwidth=50,stretch=False)
    from ui_table_copy import attach as attach_table_copy
    attach_table_copy(table, names, palette)
    table.column('availability',width=120,minwidth=105)
    table.grid(row=0,column=0,sticky='nsew')
    v=ttk.Scrollbar(frame,orient='vertical',command=table.yview);v.grid(row=0,column=1,sticky='ns')
    h=ttk.Scrollbar(frame,orient='horizontal',command=table.xview);h.grid(row=1,column=0,sticky='ew')
    table.configure(yscrollcommand=v.set,xscrollcommand=h.set)
    def local(stamp):
        return datetime.fromisoformat(stamp).astimezone(ZoneInfo('Europe/Paris')).strftime('%d/%m/%Y %H:%M:%S')
    def draw(event=None):
        if current.get('read_error'):
            if int(float(canvas.cget('height')))!=340:canvas.configure(height=340)
            canvas.delete('all')
            canvas.create_text(16,24,anchor='nw',text=current['read_error'],fill=palette['TEXT'],width=max(200,canvas.winfo_width()-32))
            canvas.bind('<Motion>',lambda event:None)
            conversion_note.configure(text='')
            return
        from home_assistant_chart import draw_chart
        selected=metrics[metric_labels.index(selected_metric.get())]
        notes=relevant_notes(conversion_notes,current['rows'],selected)
        conversion_note.configure(text=t('ha_chart_conversion_note').format(date=local(notes[0]['date'])) if notes else '')
        draw_chart(canvas,current['rows'],selected,palette,t,full_scale=full_scale.get(),raw_states=raw_states.get(),conversion_notes=notes)
    def render(rows,limited=False):
        current['read_error']=None
        current['rows']=rows
        table.delete(*table.get_children())
        now=datetime.now(timezone.utc)
        for r in rows:
            stamp=r.get('ha_value_changed_at') if r.get('timing_kind')=='ha_attribute_update' else r['ha_updated_at']
            age=(now-datetime.fromisoformat(stamp)).total_seconds() if stamp else None
            freshness='state_time_unknown' if age is None else 'future_state' if age < -300 else 'stale_state' if age>7200 else 'recent_state'
            if r.get('timing_kind')=='initial_state_uncertain':freshness='initial_uncertain'
            kind=t('ha_test_data') if r.get('test_data') else t('ha_view_observed')
            kind+=' · '+t('ha_timing_'+r.get('timing_kind','ha_state'))
            state=r.get('status')
            availability=t('ha_view_conflict') if state=='conflict' else t('ha_state_'+(state if state in ('available','unavailable','unknown') else 'unknown'))
            table.insert('', 'end', values=(local(r['ha_updated_at']),local(r['gruterra_retrieved_at']) if r.get('gruterra_retrieved_at') else '—',r['hardware_id'],t('ha_metric_'+r['metric']),r['value'] if r['value'] is not None else '—',r['unit'] or '—',availability,t('ha_freshness_'+freshness),kind))
        status.set((t('ha_view_selected_count').format(count=len(rows),metric=selected_metric.get()) if rows else t('ha_view_selected_empty').format(metric=selected_metric.get()))+(' '+t('ha_view_limit') if limited else ''))
        draw()
    def show_read_error(message):
        render([])
        current['read_error']=message
        status.set(message)
        draw()
    def refresh_associations():
        nonlocal cfg
        if demo or config is not None:return True
        previous=plant_ids[plant_selector.current()]
        valid=True
        try:
            cfg=load()
        except Exception:
            cfg={};valid=False
        mappings[:]=[row for row in cfg.get('entities',[]) if plant_id is None or row.get('plant_id')==plant_id]
        try:names=dict(plants())
        except Exception:names={}
        choices=[]
        for row in mappings:
            pid=row.get('plant_id')
            if (pid is None or type(pid) is int) and pid not in choices:choices.append(pid)
        plant_ids[:]=[plant_id] if plant_id is not None else [all_plants]+choices
        plant_labels[:]=[t('ha_view_all_plants') if pid is all_plants else t('ha_view_unassigned') if pid is None
                        else str(pid)+' — '+names.get(pid,t('ha_association_missing').format(id=pid)) for pid in plant_ids]
        plant_selector.configure(values=plant_labels)
        plant_selector.current(plant_ids.index(previous) if previous in plant_ids else 0)
        devices.clear()
        for row in mappings:
            try:
                physical=hardware_id(row.get('hardware_id'))
                devices.setdefault(physical,str(row.get('model',''))+' · …'+physical[-4:])
            except ValueError:continue
        counts=Counter(devices.values())
        for physical,label in tuple(devices.items()):
            if counts[label]>1:devices[physical]=label+' · '+physical
        change_plant(reload_view=False)
        collect_button.configure(state='normal' if mappings and valid else 'disabled')
        return valid
    def reload(event=None,refresh_config=False):
        if current['busy']:
            if refresh_config:current['config_dirty']=True
            return
        if refresh_config and not refresh_associations():
            show_read_error(t('ha_config_unreadable'));return
        try:
            selected_id=device_ids[device_labels.index(selected_device.get())]
            selected_mappings=[row for row in plant_mappings() if selected_id is None or hardware_id(row.get('hardware_id'))==selected_id]
            if demo:
                from home_assistant_demo import history
                rows=[row for row in history() if row['metric']==metrics[metric_labels.index(selected_metric.get())]
                      and (selected_id is None or row['hardware_id']==selected_id)]
            else:
                rows=read_rows(archive,selected_mappings,plant_id=plant_id,
                               metric=metrics[metric_labels.index(selected_metric.get())],limit=2001)
            render(rows[:2000],limited=len(rows)>2000)
        except Exception:
            show_read_error(t('ha_view_failed'))
    def set_busy(value):
        current['busy']=value
        for selector in (metric,device_selector):selector.configure(state='disabled' if value else 'normal')
        plant_selector.configure(state='disabled' if value or plant_id is not None else 'readonly')
        collect_button.configure(state='disabled' if value or demo or not mappings else 'normal')
    def collect():
        if demo or current['busy']:return
        if not refresh_associations():
            show_read_error(t('ha_config_unreadable'));return
        if not mappings:return
        active={**cfg,'entities':mappings}
        now=datetime.now(timezone.utc)
        try:
            saved=checkpoint(archive,active)
            start=datetime.fromisoformat(saved) if saved else now-timedelta(days=1)
            target=min(now,start+timedelta(days=7))
            plan=plan_catchup(active,archive,start=start.isoformat(),end=target.isoformat(),received_at=now.isoformat())
        except Exception:
            status.set(t('ha_catchup_plan_failed'));return
        if not plan['windows']:
            status.set(t('ha_catchup_nothing'));return
        if not messagebox.askyesno(t('ha_view_collect'),t('ha_catchup_summary').format(count=len(plan['windows']),start=plan['windows'][0]['start'],end=plan['windows'][-1]['end']),parent=window):return
        set_busy(True);status.set(t('ha_catchup_running'))
        queue=Queue()
        def worker():
            try:
                archive.parent.mkdir(parents=True,exist_ok=True)
                result=run_catchup(active,plan,archive,confirmed=True,received_at=datetime.now(timezone.utc).isoformat())
                if result.get('ok') and target < now:
                    result={**result,'code':'more_pending'}
                queue.put(result)
            except Exception:queue.put({'ok':False})
        def finished(result):
            set_busy(False)
            if current.pop('config_dirty',False):reload(refresh_config=True)
            if result.get('ok'):
                reload()
                status.set(t('ha_catchup_done').format(windows=result['completed_windows'],facts=result['facts_added'],revisions=result['revisions_added'],duplicates=result['duplicates'])+(' '+t('ha_catchup_more') if result.get('code')=='more_pending' else ''))
            else:
                if result.get('completed_windows',0):
                    reload()
                from home_assistant_feedback import failure_message
                status.set(failure_message(result))
        event_root=window._root()
        def published(result):
            if result.get('ok') or result.get('completed_windows',0):
                notifier_donnees_modifiees(event_root,exclude=window)
        threading.Thread(target=worker,daemon=True).start()
        from ui_async_result import deliver
        deliver(window,queue,finished,on_result=published,keep_after_close=True)
    collect_button=tk.Button(footer,text=t('ha_view_collect'),command=collect,state='disabled' if demo or not mappings else 'normal')
    collect_button.grid(row=0,column=0,sticky='ew')
    tk.Button(footer,text=t('ha_test_title'),command=lambda:manage_tests(window,palette)).grid(row=1,column=0,sticky='ew',pady=4)
    tk.Button(footer,text=t('ha_close'),command=window.destroy).grid(row=2,column=0,sticky='e')
    tk.Button(toolbar,text=t('ha_view_refresh'),command=lambda:reload(refresh_config=True)).pack(anchor='w',pady=6)
    canvas.bind('<Configure>',draw)
    window.bind('<<GruterraDataChanged>>',reload)
    window.bind('<<GruterraAssociationsChanged>>',lambda event:reload(refresh_config=True))
    harmoniser(window,palette)
    for selector in (metric,device_selector):
        selector.configure(bg=palette['CARD'],fg=palette['TEXT'],activebackground=palette['LIGHT_BLUE'],activeforeground=palette['TEXT'],highlightthickness=1,highlightbackground=palette['BORDER'])
        selector['menu'].configure(bg=palette['CARD'],fg=palette['TEXT'],activebackground=palette['LIGHT_BLUE'],activeforeground=palette['TEXT'])
    # Native Windows headings keep a light background even in the dark theme.
    from tkinter import ttk as themed
    style=themed.Style(window)
    style.configure(table.cget('style')+'.Heading',foreground='#223228',background='#F2F6F1')
    reload()
    if parent.winfo_toplevel().winfo_viewable():
        window.transient(parent.winfo_toplevel())
    def bring_forward():
        if window.winfo_exists():
            window.deiconify()
            window.lift()
            window.focus_set()
    window.after_idle(bring_forward)
    return window

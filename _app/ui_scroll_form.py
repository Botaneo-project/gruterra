"""Scrollable form body with fixed actions; no configuration or network access."""
def create(window,palette):
    import tkinter as tk
    from tkinter import ttk
    footer=tk.Frame(window,bg=palette['BG'])
    footer.pack(side='bottom',fill='x',padx=18,pady=10)
    area=tk.Frame(window,bg=palette['BG']);area.pack(fill='both',expand=True)
    canvas=tk.Canvas(area,bg=palette['BG'],highlightthickness=0)
    bar=ttk.Scrollbar(area,orient='vertical',command=canvas.yview)
    bar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
    canvas.configure(yscrollcommand=bar.set)
    body=tk.Frame(canvas,bg=palette['BG'])
    item=canvas.create_window(0,0,window=body,anchor='nw')
    body.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
    def resize(event):
        canvas.itemconfigure(item,width=event.width)
        for child in body.winfo_children():
            if isinstance(child,(tk.Label,tk.Checkbutton,tk.Radiobutton)):
                child.configure(wraplength=max(160,event.width-36))
    canvas.bind('<Configure>',resize)
    def wheel(event):
        if isinstance(event.widget,(tk.Text,tk.Listbox,ttk.Treeview,ttk.Combobox)):
            return
        if body.winfo_reqheight()<=canvas.winfo_height():return
        if getattr(event,'num',None) in (4,5):units=-1 if event.num==4 else 1
        else:
            delta=getattr(event,'delta',0)
            if not delta:return
            units=-int(delta/120) or (-1 if delta>0 else 1)
        canvas.yview_scroll(units,'units')
        return 'break'
    window.bind('<MouseWheel>',wheel,add='+')
    window.bind('<Button-4>',wheel,add='+');window.bind('<Button-5>',wheel,add='+')
    return body,footer


def create_table(parent, palette, *, columns, height, padx=0, pady=0):
    """Table with native scrolling on both axes, inside a scrolling form."""
    import tkinter as tk
    from tkinter import ttk
    frame = tk.Frame(parent, bg=palette['BG'])
    frame.pack(fill='x', padx=padx, pady=pady)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    table = ttk.Treeview(frame, columns=columns, show='headings', height=height)
    vertical = ttk.Scrollbar(frame, orient='vertical', command=table.yview)
    horizontal = ttk.Scrollbar(frame, orient='horizontal', command=table.xview)
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    table.grid(row=0, column=0, sticky='nsew')
    vertical.grid(row=0, column=1, sticky='ns')
    horizontal.grid(row=1, column=0, sticky='ew')
    return table


def create_text(parent, palette, *, height, padx=0, pady=0):
    """Copyable report with its own scrollbar; wheel stays in the report."""
    import tkinter as tk
    from tkinter import ttk
    frame = tk.Frame(parent, bg=palette['BG'])
    frame.pack(fill='both', expand=True, padx=padx, pady=pady)
    text = tk.Text(frame, height=height, wrap='word', bg=palette['BG'],
                   fg=palette['TEXT'], relief='flat', font=('Segoe UI', 9),
                   insertbackground=palette['TEXT'])
    bar = ttk.Scrollbar(frame, orient='vertical', command=text.yview)
    text.configure(yscrollcommand=bar.set)
    bar.pack(side='right', fill='y')
    text.pack(side='left', fill='both', expand=True)
    return text

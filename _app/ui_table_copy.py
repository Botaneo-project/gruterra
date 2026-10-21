"""Copy displayed selections only; never exports hidden technical columns."""
import csv
import io


def selected_text(table,columns):
    selected=set(table.selection())
    rows=[item for item in table.get_children('') if item in selected]
    if not rows:return ''
    stream=io.StringIO(newline='')
    writer=csv.writer(stream,delimiter='\t',lineterminator='\n')
    writer.writerow([table.heading(column,'text') for column in columns])
    writer.writerows([[table.set(item,column) for column in columns] for item in rows])
    return stream.getvalue()


def attach(table,columns,palette):
    import tkinter as tk
    from i18n import traduire_courant as t
    columns=tuple(columns)
    menu=tk.Menu(table,tearoff=False,bg=palette['CARD'],fg=palette['TEXT'],
                 activebackground=palette.get('LIGHT_BLUE',palette['BG']),activeforeground=palette['TEXT'])
    def copy(event=None):
        text=selected_text(table,columns)
        if text:
            table.clipboard_clear();table.clipboard_append(text)
        return 'break'
    menu.add_command(label=t('table_copy_selected_one'),command=copy)
    def popup(event):
        row=table.identify_row(event.y)
        if not row:return 'break'
        if row not in table.selection():table.selection_set(row)
        table.focus(row);table.focus_set()
        menu.entryconfigure(0,label=t('table_copy_selected_one' if len(table.selection())==1 else 'table_copy_selected_many'))
        try:menu.tk_popup(event.x_root,event.y_root)
        finally:menu.grab_release()
        return 'break'
    table.configure(selectmode='extended')
    table.bind('<Button-3>',popup,add='+')
    table.bind('<Control-c>',copy,add='+');table.bind('<Control-C>',copy,add='+')
    # Keyboard equivalent of the context menu, anchored to the focused row.
    def keyboard_menu(event):
        rows=table.selection()
        if not rows:return 'break'
        box=table.bbox(table.focus() or rows[0])
        if not box:return 'break'
        from types import SimpleNamespace
        return popup(SimpleNamespace(y=box[1]+box[3]//2,x_root=table.winfo_rootx()+box[0]+12,y_root=table.winfo_rooty()+box[1]+box[3]))
    table.bind('<Shift-F10>',keyboard_menu,add='+')
    return {'menu':menu,'copy':copy,'popup':popup}

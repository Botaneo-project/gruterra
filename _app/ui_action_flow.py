"""Wrap action buttons to the actual available width."""
def reflow_actions(frame):
    children = frame.winfo_children()
    for child in children:
        child.pack_forget()
    def layout(event=None):
        width = event.width if event else frame.winfo_width()
        if width < 2:
            return
        y = used = row_height = 0
        for child in children:
            requested = child.winfo_reqwidth() + 8
            if used and used + requested > width:
                y += row_height
                used = row_height = 0
            child.place(x=used, y=y + 4)
            row_height = max(row_height, child.winfo_reqheight() + 8)
            used += requested
        frame.configure(height=y + row_height)
    frame.bind('<Configure>', layout, add='+')
    frame.after_idle(layout)

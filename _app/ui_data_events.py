"""Notify live data views on Tk's main thread, from any application window."""


def _descendants(parent,event_name,exclude=None):
    for child in tuple(parent.winfo_children()):
        if not child.winfo_exists():continue
        if child.winfo_toplevel() is child and child is not exclude:
            child.event_generate(event_name,when='tail')
        _descendants(child,event_name,exclude)


def notifier_donnees_modifiees(parent,event_name='<<GruterraDataChanged>>',*,exclude=None):
    root=parent._root()
    root.event_generate(event_name,when='tail')
    _descendants(root,event_name,exclude)


def notifier_associations_modifiees(parent):
    notifier_donnees_modifiees(parent,'<<GruterraAssociationsChanged>>')

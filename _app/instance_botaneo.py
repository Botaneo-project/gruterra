"""Verrou interprocessus conserve jusqu'a la fermeture de Gruterra."""

from i18n import traduire_courant as _tr
import atexit
import os
from pathlib import Path
from botaneo_config import CONFIG_DIR


class InstanceOccupee(RuntimeError):
    pass


class VerrouInstance:
    def __init__(self, path=None):
        # The updater coordinates the real app through the historical root lock.
        # Only the demo gets its own lock; custom settings must not bypass it.
        default_dir = CONFIG_DIR if os.environ.get('BOTANEO_DEMO') == '1' else Path(__file__).resolve().parent.parent / '_config'
        self.path = Path(path) if path else default_dir / 'botaneo.instance.lock'
        self.file = None

    def acquerir(self):
        if self.file is not None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = open(self.path, 'a+b')
        try:
            if stream.seek(0, 2) == 0:
                stream.write(b'0')
                stream.flush()
            stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            stream.close()
            raise InstanceOccupee(_tr('instance_botaneo_text_34')) from None
        self.file = stream

    def liberer(self):
        if self.file is not None:
            self.file.close()
            self.file = None


_verrou = VerrouInstance()
atexit.register(_verrou.liberer)


def exiger_instance_unique(graphique=False):
    try:
        if (Path(__file__).resolve().parent.parent / '_security_backups' / 'update-pending.json').exists():
            raise InstanceOccupee(_tr('update_recovery_required'))
        _verrou.acquerir()
    except (InstanceOccupee, OSError) as erreur:
        message = str(erreur) if isinstance(erreur, InstanceOccupee) else _tr('instance_botaneo_text_51')
        if graphique:
            import tkinter as tk
            from tkinter import messagebox
            fenetre = tk.Tk()
            fenetre.withdraw()
            messagebox.showinfo('Gruterra', message, parent=fenetre)
            fenetre.destroy()
        else:
            print(message)
        raise SystemExit(1)

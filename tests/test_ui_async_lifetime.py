from pathlib import Path
import sys
import tkinter as tk
from queue import Queue
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from ui_async_result import deliver
from ui_data_events import notifier_donnees_modifiees

def tick(root,milliseconds=35):
    done=tk.BooleanVar(root,value=False);root.after(milliseconds,lambda:done.set(True));root.wait_variable(done);root.update()

class AsyncLifetimeTests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.root.geometry('120x80');self.root.update()
        self.addCleanup(self.root.destroy)
    def test_open_window_gets_exactly_one_result_without_leftover_timer(self):
        win=tk.Toplevel(self.root);self.root.update();pending=Queue();callback=Mock();published=Mock()
        deliver(win,pending,callback,on_result=published,interval=5)
        pending.put({'ok':True});tick(self.root)
        callback.assert_called_once_with({'ok':True});published.assert_called_once_with({'ok':True})
        self.assertEqual(len(self.root.tk.call('after','info')),0)
        tick(self.root);self.assertEqual(callback.call_count,1)
    def test_closed_preview_cancels_delivery(self):
        win=tk.Toplevel(self.root);self.root.update();pending=Queue();callback=Mock();published=Mock()
        deliver(win,pending,callback,on_result=published,interval=5)
        win.destroy();pending.put({'ok':True});tick(self.root)
        callback.assert_not_called();published.assert_not_called()
        self.assertEqual(len(self.root.tk.call('after','info')),0)
    def test_closed_recovery_still_notifies_live_windows_but_never_calls_closed_ui(self):
        origin=tk.Toplevel(self.root);sibling=tk.Toplevel(self.root);nested=tk.Toplevel(sibling);self.root.update()
        seen=[]
        for name,window in (('home',self.root),('sibling',sibling),('nested',nested)):
            window.bind('<<GruterraDataChanged>>',lambda event,name=name:seen.append(name))
        pending=Queue();callback=Mock()
        deliver(origin,pending,callback,on_result=lambda result:notifier_donnees_modifiees(sibling),keep_after_close=True,interval=5)
        origin.destroy();pending.put({'ok':True});tick(self.root)
        callback.assert_not_called()
        self.assertEqual(sorted(seen),['home','nested','sibling'])
        self.assertEqual(len(self.root.tk.call('after','info')),0)
    def test_origin_can_be_excluded_to_preserve_completion_notice(self):
        origin=tk.Toplevel(self.root);sibling=tk.Toplevel(self.root);self.root.update();seen=[]
        origin.bind('<<GruterraDataChanged>>',lambda event:seen.append('origin'))
        sibling.bind('<<GruterraDataChanged>>',lambda event:seen.append('sibling'))
        notifier_donnees_modifiees(origin,exclude=origin);self.root.update()
        self.assertEqual(seen,['sibling'])

if __name__=='__main__':unittest.main()

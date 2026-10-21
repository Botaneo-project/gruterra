"""Deliver worker results on Tk's main thread, with explicit window lifetime."""
from queue import Empty


def deliver(window, pending, callback, *, on_result=None, keep_after_close=False, interval=100):
    root=window._root()
    state={'timer':None,'done':False}
    def cleanup():
        state['done']=True
        timer=state.pop('timer',None)
        if timer:
            try:root.after_cancel(timer)
            except Exception:pass
        if window.winfo_exists():
            window.unbind('<Destroy>',binding)
    def poll():
        state['timer']=None
        if state['done']:return
        if not keep_after_close and not window.winfo_exists():
            cleanup();return
        try:result=pending.get_nowait()
        except Empty:
            state['timer']=root.after(interval,poll);return
        cleanup()
        try:
            if on_result:on_result(result)
        finally:
            if window.winfo_exists():callback(result)
    def destroyed(event):
        if event.widget is window and not keep_after_close:cleanup()
    binding=window.bind('<Destroy>',destroyed,add='+')
    state['timer']=root.after(interval,poll)
    return cleanup

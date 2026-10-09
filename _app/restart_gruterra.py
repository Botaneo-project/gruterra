"""Relance une seule instance après la fin effective du processus précédent."""
from __future__ import annotations
import argparse
import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path


def attendre_fin_processus(pid, timeout=120):
    if pid <= 0 or pid == os.getpid():
        raise ValueError("Invalid parent process")
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.WaitForSingleObject.restype = ctypes.c_ulong
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x00100000, False, pid)
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:
                return True
            raise ctypes.WinError(error)
        try:
            result = kernel.WaitForSingleObject(handle, int(timeout * 1000))
            if result == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
            return result == 0
        finally:
            kernel.CloseHandle(handle)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    return False


def relancer_apres_sortie(pid, mode, racine, timeout=120):
    script = Path(racine) / ("Lancer_Demo.py" if mode == "demo" else "Lancer_Gruterra.py")
    if not script.is_file():
        raise FileNotFoundError(script)
    if not attendre_fin_processus(pid, timeout):
        raise TimeoutError("Previous Gruterra process has not exited; restart cancelled")
    subprocess.Popen([sys.executable, str(script)], cwd=str(racine), env=os.environ.copy(),
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-pid", type=int, required=True)
    parser.add_argument("--mode", choices=("demo", "real"), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        relancer_apres_sortie(args.parent_pid, args.mode, root)
    except (OSError, ValueError) as error:
        config = Path(os.environ.get("BOTANEO_CONFIG_DIR", str(root / "_config")))
        config.mkdir(parents=True, exist_ok=True)
        (config / "update_restart.log").write_text(str(error) + "\n", encoding="utf-8")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

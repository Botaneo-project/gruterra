"""Windows current-user DPAPI, no plaintext fallback or extra password."""
import base64
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
from botaneo_config import lire_json, ecrire_json

STORAGE = 'windows_dpapi_current_user_v1'


def _crypt(value, *, decrypt=False):
    if os.name != 'nt':
        raise ValueError('secure_storage_unavailable')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(value)
    source = Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        function = crypt.CryptUnprotectData
        function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        args = (ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output))
    else:
        function = crypt.CryptProtectData
        function.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        args = (ctypes.byref(source), 'Gruterra Home Assistant', None, None, None, 1, ctypes.byref(output))
    function.restype = wintypes.BOOL
    if not function(*args):
        raise ValueError('secret_unavailable')
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        if output.data:
            ctypes.memset(output.data, 0, output.size)
            kernel.LocalFree(ctypes.cast(output.data, ctypes.c_void_p))


def protect(token):
    if not isinstance(token, str) or len(token) > 8192 or any(char.isspace() for char in token):
        raise ValueError('invalid_credentials')
    return base64.b64encode(_crypt(token.encode('utf-8'))).decode('ascii') if token else ''


def unprotect(encoded):
    try:
        if not isinstance(encoded, str) or len(encoded) > 65536:
            raise ValueError()
        return _crypt(base64.b64decode(encoded, validate=True), decrypt=True).decode('utf-8') if encoded else ''
    except Exception:
        raise ValueError('secret_unavailable') from None


def write_private(path, config):
    """Encrypt before any disk write. Atomic save leaves old file on failure."""
    data = dict(config)
    token = data.pop('access_token', '')
    data.pop('_secret_unavailable', None)
    data['access_token_protected'] = protect(token)
    data['secret_storage'] = STORAGE
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ecrire_json(path, data)


def read_private(path, *, migrate=True):
    data = lire_json(path)
    if 'access_token' in data:
        # Legacy plaintext is removed atomically; it is not copied to a backup.
        if not isinstance(data['access_token'], str):
            raise ValueError('invalid_credentials')
        if migrate:
            write_private(path, data)
        return data
    if data.get('secret_storage') != STORAGE:
        raise ValueError('invalid_config')
    try:
        token = unprotect(data.get('access_token_protected', ''))
    except ValueError:
        # Preserve encrypted file. User may replace a lost token after reinstall.
        return {**data, 'access_token': '', '_secret_unavailable': True}
    return {**data, 'access_token': token}

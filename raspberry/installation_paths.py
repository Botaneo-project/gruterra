"""Resolve the installation home for both deployed and source-tree utilities."""
import os
from pathlib import Path


def installation_root():
    configured = os.environ.get('BOTANEO_HOME')
    if configured:
        root = Path(configured).expanduser()
        if not root.is_absolute():
            raise ValueError('BOTANEO_HOME must be an absolute path')
        return root
    here = Path(__file__).resolve().parent
    # The installer deploys this module alongside all utilities in collector/.
    return here.parent if here.name == 'collector' else Path.home() / 'botaneo'

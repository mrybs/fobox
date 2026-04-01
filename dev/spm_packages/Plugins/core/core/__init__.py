from slinn.slinn_app_api import SlinnAppAPI
from .version import version as fobox_version
import sys
import importlib


app = SlinnAppAPI('.', package=__package__)


if 'core.api' not in sys.modules.keys():
    from core.api import dp
else:
    dp = importlib.reload(sys.modules['core.api']).dp

print(f'Running on {fobox_version}')

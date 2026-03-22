from slinn.slinn_app_api import SlinnAppAPI
import sys, importlib


app = SlinnAppAPI('.', package=__package__)


if 'core.api' not in sys.modules.keys():
    from core.api import dp
else:
    dp = importlib.reload(sys.modules['core.api']).dp

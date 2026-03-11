from slinn.slinn_app_api import SlinnAppAPI
import sys, importlib


app = SlinnAppAPI('.', package=__package__)


if 'app.app' not in sys.modules.keys():
    from app.app import dp
else:
    dp = importlib.reload(sys.modules['app.app']).dp

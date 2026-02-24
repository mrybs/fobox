from slinn.slinn_app_api import SlinnAppAPI
import sys, importlib


app = SlinnAppAPI('./auth')


if 'auth.app' not in sys.modules.keys():
    from auth.app import dp
else:
    dp = importlib.reload(sys.modules['auth.app']).dp

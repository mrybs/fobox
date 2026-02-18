from slinn.slinn_app_api import SlinnAppAPI
import sys, importlib


app = SlinnAppAPI('./fobox')


if 'fobox.app' not in sys.modules.keys():
    from fobox.app import dp
else:
    dp = importlib.reload(sys.modules['fobox.app']).dp

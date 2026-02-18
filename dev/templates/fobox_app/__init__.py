from slinn.slinn_app_api import SlinnAppAPI
import sys, importlib


if 'example.app' not in sys.modules.keys():
    from example.app import dp
else:
    dp = importlib.reload(sys.modules['example.app']).dp


app = SlinnAppAPI()

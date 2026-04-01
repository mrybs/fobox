from slinn.slinn_app_api import SlinnAppAPI
import sys, importlib


app = SlinnAppAPI('./screenshoter_adapter')


if 'screenshoter_adapter.app' not in sys.modules.keys():
    from screenshoter_adapter.app import dp
else:
    dp = importlib.reload(sys.modules['screenshoter_adapter.app']).dp

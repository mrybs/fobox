from slinn.slinn_app_api import SlinnAppAPI
import sys, importlib


app = SlinnAppAPI('./admin')


if 'admin.app' not in sys.modules.keys():
    from admin.app import dp
else:
    dp = importlib.reload(sys.modules['admin.app']).dp

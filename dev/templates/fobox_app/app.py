from slinn import ApiDispatcher, AsyncRequest, HttpResponse, Storage, AnyFilter
from orm.postgres import Postgres
from orm import get_driver_name
from slinn_api import SlinnAPI
from . import app
import geety as G
import re
import json


dp = ApiDispatcher()
gapp = G.App(context={
    'PNAME': SlinnAPI.get_config()['name']
})

for db in SlinnAPI.get_config()['dbs']:
    match get_driver_name(db['dsn']):
        case 'postgres':
            gapp.add_database_pool(Postgres(
                db['dsn'],
                server_settings=db['server_settings']
            ))

views = Storage(app.path + '/views')
palletes = Storage(app.path + '/../Palletes')

def reload_components():
    gapp.components = {}
    palletes_json = {}
    with palletes('palletes.json', 'r') as palletes_json_f:
        palletes_json = json.loads(palletes_json_f.read())
    for pallete in palletes_json['palletes']:
        if palletes.isdir(pallete['path']):
            for components_fn in palletes.listdir(pallete['path']):
                with palletes(pallete['path'] + '/' + components_fn, 'r') as components:
                    gapp.load(components)

# Write your code down here
@dp(AnyFilter)
async def index(request: AsyncRequest):
    reload_components()
    request.link = request.link.removeprefix('/') or 'index'

    if re.search(r'\.\.', request.link):
        return 403

    if not views.isfile(request.link+'.view.xml') and not views.isfile(request.link):
        return 404
    
    if '.' in request.link:
        with views(request.link, 'rb', 'utf-8') as file:
            await request.respond(HttpResponse, file.read(), content_type=G.MIME_TYPES.get(request.link.split('.')[-1], 'text/plain'))
    else:
        with views(request.link+'.view.xml', 'r', 'utf-8') as view:
            page = gapp.new_page(view)
            page.set_entry_point('View')
            await request.respond(HttpResponse, await page.html(), content_type='text/html; charset=utf-8')

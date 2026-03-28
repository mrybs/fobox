from slinn import ApiDispatcher, AsyncRequest, HttpResponse, Storage, AnyFilter, ProjectAPI
from orm.postgres import Postgres
from orm import get_driver_name
from . import app
import geety as G
import re
import json


dp = ApiDispatcher()
gapp = G.App(context={
    'PNAME': ProjectAPI.get_config()['name']
})
storages = {
    'palletes': [],
    'themes': [],
}
for plugin in ProjectAPI.get_plugins():
    storage = ProjectAPI.get_plugin_storage(plugin)
    for key in storages:
        if storage.isdir(key):
            storages[key].append(storage.substorage(key))

for db in ProjectAPI.get_config()['dbs']:
    match get_driver_name(db['dsn']):
        case 'postgres':
            gapp.add_database_pool(Postgres(
                db['dsn'],
                server_settings=db['serverSettings']
            ))

views = Storage('views', package=__package__)

def reload_components():
    gapp.components = {}
    palletes_json = {}
    for palletes in storages['palletes']:
        with palletes('palletes.json', 'r') as palletes_json_f:
            palletes_json = json.loads(palletes_json_f.read())
        for pallete in palletes_json['palletes']:
            if palletes.isdir(pallete['path']):
                for components_fn in palletes.listdir(pallete['path']):
                    if components_fn.endswith('.xml'):
                        with palletes(pallete['path'] + '/' + components_fn, 'r') as components:
                            gapp.load(components)

single_themes = {}

def reload_themes():
    for themes in storages['themes']:
        for theme in themes.listdir('.'):
            single_themes[theme] = themes.substorage(theme)

def load_theme(theme):
    storage = single_themes[theme]
    css = ''
    for file in storage.listdir('.'):
        with storage(file, 'r') as f:
            css += f.read()
    return css


reload_themes()
current_theme = load_theme('miot')

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
            page.add_style(current_theme)
            await request.respond(HttpResponse, await page.html(), content_type='text/html; charset=utf-8')

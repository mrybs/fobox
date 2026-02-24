from slinn import ApiDispatcher, AsyncRequest, HttpResponse, Storage, AnyFilter
from orm.postgres import Postgres
from orm import get_driver_name
from slinn_api import SlinnAPI
from . import app
import geety as G
import re


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
components = Storage(app.path + '/../components')
for component_file in components.listdir('.'):
    if components.isfile(component_file):
        with components(component_file, 'r') as component:
            gapp.load(component)

# Write your code down here
@dp(AnyFilter)
async def index(request: AsyncRequest):
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

from slinn import ApiDispatcher, AsyncRequest, HttpResponse, Storage
from orm.postgres import Postgres
from orm import get_driver_name
from slinn_api import SlinnAPI
from . import app
import geety as G


dp = ApiDispatcher('localhost', prefix='fobox')
gapp = G.App()

for db in app.config['dbs']:
    match get_driver_name(db['dsn']):
        case 'postgres':
            gapp.add_database_pool(Postgres(
                db['dsn'],
                server_settings=db['server_settings']
            ))

views = Storage(app.path + '/views')
components = Storage(app.path + '/components')
for component_file in components.listdir('.'):
    if components.isfile(component_file):
        with components(component_file, 'r') as component:
            gapp.load(component)


@dp.get()
async def index(request: AsyncRequest):
    with views('main.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('App')
        await request.respond(HttpResponse, await page.html(context={'users': ['mrybs', '001kpp', 'test', 'мбырс', 'чинчопа <3 <br/>']}), content_type='text/html; charset=utf-8')


@dp.get('recreate_app')
async def recreate_app(request: AsyncRequest):
    SlinnAPI.delete_app(request.args['name'])
    SlinnAPI.create_app_from_template(
        name=request.args['name'],
        template_name='fobox_app',
        templates_folder='templates'
    )
    await request.respond(HttpResponse, f'app {request.args['name']} has recreated')
    SlinnAPI.restart()


@dp.get('create_app')
async def create_app(request: AsyncRequest):
    SlinnAPI.create_app_from_template(
        name=request.args['name'],
        template_name='fobox_app',
        templates_folder='templates'
    )
    await request.respond(HttpResponse, f'app {request.args['name']} has created')
    SlinnAPI.restart()

@dp.get('delete_app')
async def delete_app(request: AsyncRequest):
    SlinnAPI.delete_app(request.args['name'])
    await request.respond(HttpResponse, f'app {request.args['name']} has deleted')
    SlinnAPI.restart()

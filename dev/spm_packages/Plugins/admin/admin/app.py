from slinn import ApiDispatcher, AsyncRequest, HttpResponse, Storage, HttpRedirect, HttpRender, IMiddleware, HttpJSONResponse, ProjectAPI
from slinn.utils import optional
from . import app
from .db_init import gapp, fobox_db
from core.middlewares import AuthMiddleware
import functools
import json
import urllib.parse
import geety as G


dp = ApiDispatcher('localhost', prefix='fobox')
views = Storage('views', package=__package__)
components = Storage('Components', package=__package__)
site_app = Storage('app')

palletes_storages = []
for plugin in ProjectAPI.get_plugins():
    storage = ProjectAPI.get_plugin_storage(plugin)
    if storage.isdir('palletes'):
        palletes_storages.append(storage.substorage('palletes'))


class AdminOnly(IMiddleware):
    def __init__(self):
        super().__init__()

    def __call__(self, func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if 'user' not in kwargs:
                return 401
            if kwargs['user'].role != 2:
                return 404
            return await optional(func, *args, **kwargs)

        return wrapper


def reload_components():
    gapp.components = {}
    for component_file in components.listdir('.'):
        if components.isfile(component_file):
            with components(component_file, 'r') as component:
                gapp.load(component)

def reload_palletes():
    palletes_json = {}
    palletes_all = {}
    for palletes in palletes_storages:
        with palletes('palletes.json', 'r') as palletes_json_f:
            palletes_json = json.loads(palletes_json_f.read())
        for pallete in palletes_json['palletes']:
            if palletes.isdir(pallete['path']):
                for components_fn in palletes.listdir(pallete['path']):
                    with palletes(pallete['path'] + '/' + components_fn, 'r') as components:
                        if pallete['path'] not in palletes_all:
                            palletes_all[pallete['path']] = []
                        palletes_all[pallete['path']].append(components.read())
    return palletes_json, palletes_all


@dp.get()
@AuthMiddleware(fobox_db)
@AdminOnly()
async def index(request: AsyncRequest, user: dict):
    reload_components()
    with views('index.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('View')
        await request.respond(HttpResponse, await page.html(context={
            'USER': user
        }), content_type='text/html; charset=utf-8')

@dp.get('pages')
@AuthMiddleware(fobox_db)
@AdminOnly()
async def pages(request: AsyncRequest, user: dict):
    reload_components()
    with views('pages.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('View')
        await request.respond(HttpResponse, await page.html(context={
            'USER': user,
            'ROOT': ProjectAPI.get_link()
        }), content_type='text/html; charset=utf-8')

@dp.get('editor/<str view>')
@AuthMiddleware(fobox_db)
@AdminOnly()
async def editor(request: AsyncRequest, user: dict, view: str):
    reload_components()
    with views('editor.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('View')
        await request.respond(HttpResponse, await page.html(context={
            'COMPONENTS': [
                {
                    'name': key
                } for key in gapp.components
            ],
            'USER': user
        }), content_type='text/html; charset=utf-8')

@dp.get('api/pages')
@AuthMiddleware(fobox_db, api=True)
@AdminOnly()
async def get_pages(request: AsyncRequest, user: dict):
    async with await fobox_db.acquire() as conn:
        await request.respond(HttpResponse, json.dumps(
            [
                {
                    'path': page['path'],
                    'creator_id': page['creator_id'],
                    'enabled': page['enabled'],
                    'created_at': page['created_at'].timestamp(),
                    'updated_at': page['updated_at'].timestamp()
                }
                for page in await conn._fobox_pages.find({})
            ], ensure_ascii=False
        ))

@dp.post('api/pages/<str path>')
@AuthMiddleware(fobox_db, api=True)
@AdminOnly()
async def create_page(request: AsyncRequest, user: dict, path: str):
    async with await fobox_db.acquire() as conn:
        if await conn._fobox_pages.count({ 'path': path }):
            await request.respond(
                HttpJSONResponse,
                status='failed',
                message=f'page {path} exists'
            )
            return
        await conn._fobox_pages.insert({
            'path': path,
            'creator_id': user['id']
        })
        await request.respond(HttpJSONResponse, status='ok')


@dp.delete('api/pages/<str path>')
@AuthMiddleware(fobox_db, api=True)
@AdminOnly()
async def delete_page(request: AsyncRequest, user: dict, path: str):
    async with await fobox_db.acquire() as conn:
        if not await conn._fobox_pages.count({ 'path': path }):
            await request.respond(
                HttpJSONResponse,
                status='failed',
                message=f'page {path} not exists'
            )
            return
        await conn._fobox_pages.delete({ 'path': path })
        await request.respond(HttpJSONResponse, status='ok')


@dp.get('palletes')
@AuthMiddleware(fobox_db, api=True)
@AdminOnly()
async def get_palletes(request: AsyncRequest, user: dict):
    palletes_json, palletes_all = reload_palletes()
    await request.respond(HttpResponse, json.dumps(
        palletes_json, ensure_ascii=False
    ))

@dp.get('palletes/<str path>')
@AuthMiddleware(fobox_db, api=True)
@AdminOnly()
async def get_pallete(request: AsyncRequest, user: dict, path: str):
    palletes_json, palletes_all = reload_palletes()
    if path not in palletes_all:
        return 404
    result = {
        'components': []
    }
    for component in palletes_all[path]:
        component = ''.join([line.strip()+'\n' for line in component.split('\n')])
        result['components'].append(component)
    await request.respond(HttpJSONResponse, **result)

@dp.post('savePage/<str path>')
@AuthMiddleware(fobox_db, api=True)
@AdminOnly()
async def save_view(request: AsyncRequest, user: dict, path: str):
    async with await fobox_db.acquire() as conn:
        if not await conn._fobox_pages.count({'path': path}):
            await request.respond(
                HttpJSONResponse,
                status='failed',
                message=f'page {path} exists'
            )
            return
    xml = await request.body.get()
    with site_app(f'views/{path}.view.xml', 'wb') as f:
        f.write(xml)
    await request.respond(HttpJSONResponse, status='ok')

@dp.get('loadPage/<str path>')
@AuthMiddleware(fobox_db, api=True)
@AdminOnly()
async def load_view(request: AsyncRequest, user: dict, path: str):
    if site_app.isfile(f'views/{path}.view.xml'):
        await request.respond(HttpRender, f'views/{path}.view.xml', storage=site_app)
    else:
        return 404

@dp.get('ping')
async def ping(request: AsyncRequest):
    async with await fobox_db.acquire() as conn:
        await conn.collections()
    await request.respond(HttpResponse, 'pong')


dp  .static('/styles/root.css', HttpRender, 'styles/root.css', storage=views)\
    .static('/styles/modal.css', HttpRender, 'styles/modal.css', storage=views)\
    .static('/styles/styles.css', HttpRender, 'styles/styles.css', storage=views)\
    .static('/scripts/editor/canvas.js', HttpRender, 'scripts/editor/canvas.js', storage=views)\
    .static('/scripts/editor/component.js', HttpRender, 'scripts/editor/component.js', storage=views)\
    .static('/scripts/editor/contextmenu.js', HttpRender, 'scripts/editor/contextmenu.js', storage=views)\
    .static('/scripts/editor/misc.js', HttpRender, 'scripts/editor/misc.js', storage=views)\
    .static('/scripts/editor/pallete.js', HttpRender, 'scripts/editor/pallete.js', storage=views)\
    .static('/scripts/editor/parser.js', HttpRender, 'scripts/editor/parser.js', storage=views)\
    .static('/scripts/editor/properties.js', HttpRender, 'scripts/editor/properties.js', storage=views)\
    .static('/scripts/editor/property.js', HttpRender, 'scripts/editor/property.js', storage=views)\
    .static('/scripts/editor/trash.js', HttpRender, 'scripts/editor/trash.js', storage=views)\
    .static('/styles/editor/canvas.css', HttpRender, 'styles/editor/canvas.css', storage=views)\
    .static('/styles/editor/component.css', HttpRender, 'styles/editor/component.css', storage=views)\
    .static('/styles/editor/contextmenu.css', HttpRender, 'styles/editor/contextmenu.css', storage=views)\
    .static('/styles/editor/pallete.css', HttpRender, 'styles/editor/pallete.css', storage=views)\
    .static('/styles/editor/properties.css', HttpRender, 'styles/editor/properties.css', storage=views)\
    .static('/styles/editor/root.css', HttpRender, 'styles/editor/root.css', storage=views)\
    .static('/styles/editor/trash.css', HttpRender, 'styles/editor/trash.css', storage=views)\
    .static('/scripts/editor.js', HttpRender, 'scripts/editor.js', storage=views)\
    .static('/scripts/modal.js', HttpRender, 'scripts/modal.js', storage=views)\
    .static('/res/cover.png', HttpRender, 'res/cover.png', storage=views)

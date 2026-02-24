from slinn import ApiDispatcher, AsyncRequest, HttpResponse, Storage, HttpRedirect, HttpRender, IMiddleware
from slinn_api import SlinnAPI
from slinn.utils import optional
from . import app
from .db_init import gapp, fobox_db
import functools
import json
import urllib.parse


dp = ApiDispatcher('localhost', prefix='fobox')
views = Storage(app.path + '/views')
components = Storage(app.path + '/../components')


class AuthMiddleware(IMiddleware):
    def __init__(self):
        super().__init__()

    def __call__(self, func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            user = await get_user(kwargs['request'])
            if not user:
                return HttpRedirect(f'/auth?redirect_uri={urllib.parse.quote(kwargs['request'].full_link)}')
            return await optional(func, *args, **(kwargs|{'user': user}))

        return wrapper

class AdminOnly(IMiddleware):
    def __init__(self):
        super().__init__()

    def __call__(self, func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
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


async def get_user(request: AsyncRequest):
    token = request.args.get('token', '') or \
            request.cookies.get('Token', '') or \
            (
                request.headers['Authorization'].removeprefix('Bearer ')
                if 'Authorization' in request.headers.keys() else ''
            )
    if not token:
        return None
    async with await fobox_db.acquire() as conn:
        session = await conn._fobox_active_sessions.find_one({
            'token': token
        })
        if not session:
            return None
        return await conn._fobox_users.find_one({
            'id': session['user_id']
        })


@dp.get()
@AuthMiddleware()
@AdminOnly()
async def index(request: AsyncRequest, user: dict):
    reload_components()
    with views('index.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('View')
        await request.respond(HttpResponse, await page.html(context={
            'USER': user
        }), content_type='text/html; charset=utf-8')

@dp.get('editor')
@AuthMiddleware()
@AdminOnly()
async def editor(request: AsyncRequest, user: dict):
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

@dp.get('ping')
async def ping(request: AsyncRequest):
    async with await fobox_db.acquire() as conn:
        await conn.collections()
    await request.respond(HttpResponse, 'pong')


dp.static('/scripts/geety.js', HttpRender, 'scripts/geety.js', storage=views)
dp.static('/styles/root.css', HttpRender, 'styles/root.css', storage=views)


from slinn import ApiDispatcher, AsyncRequest, Storage, HttpResponse, HttpGETRedirect, HttpJSONResponse, HttpRender
from . import app
from orm.postgres import Postgres
from orm import get_driver_name
from slinn_api import SlinnAPI
import geety as G
import datetime
import secrets
import urllib.parse
import bcrypt
import json
import email_tools
import string
import re


EMAIL_PATTERN = re.compile(r"""(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])""")


dp = ApiDispatcher(prefix=app.config['prefix'])
gapp = G.App(context={
    'PNAME': SlinnAPI.get_config()['name']
})
views = Storage(app.path + '/views')
components = Storage(app.path + '/Components')

for db in SlinnAPI.get_config()['dbs']:
    match get_driver_name(db['dsn']):
        case 'postgres':
            gapp.add_database_pool(Postgres(
                db['dsn'],
                server_settings=db['server_settings']
            ))
db = gapp.db_pools[0]

def reload_components():
    gapp.components = {}
    for component_file in components.listdir('.'):
        if components.isfile(component_file):
            with components(component_file, 'r') as component:
                gapp.load(component)

# Write your code down here
@dp.get()
async def auth(request: AsyncRequest):
    reload_components()
    with views('auth.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('View')
        await request.respond(HttpResponse, await page.html(context={
            'GET_ARGS': request.args
        }), content_type='text/html; charset=utf-8')

@dp.post()
async def auth_post(request: AsyncRequest):
    form = await request.body.form()
    if 'login' not in form or 'password' not in form:
        return HttpGETRedirect(
                f'/auth'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Форма не заполнена')}'
            )
    async with await db.acquire() as conn:
        user = await conn._fobox_users.find_one({
            'email': form['login']
        }) or (await conn._fobox_users.find_one({
            'id': int(form['login'])
        }) if form['login'].isdigit() else None)
        if user is None:
            return HttpGETRedirect(
                f'/auth'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Логин не соответствует ни одному пользователю')}'
            )
        if not bcrypt.checkpw(form['password'].encode(), user['password_hash'].encode()):
            return HttpGETRedirect(
                f'/auth'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Пароль неверный')}'
            )
        token = secrets.token_urlsafe(32)
        await conn._fobox_sessions.insert({
            'token': token,
            'user_id': user['id']
        })
        return HttpGETRedirect(request.args.get('redirect_uri', '/')).set_cookie(
            key='Token',
            value=token,
            expires=None if form.get('foreign_device') else datetime.datetime.now() + datetime.timedelta(weeks=2)
        )

@dp.get('signup')
async def signup(request: AsyncRequest):
    reload_components()
    with views('signup.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('View')
        await request.respond(HttpResponse, await page.html(context={
            'GET_ARGS': request.args
        }), content_type='text/html; charset=utf-8')

@dp.post('send_code')
async def send_code(request: AsyncRequest):
    data = json.loads(await request.body.get())
    if 'email' not in data or not EMAIL_PATTERN.fullmatch(data['email']):
        return 400
    code = ''.join([secrets.choice(string.digits) for _ in range(6)])
    async with await db.acquire() as conn:
        await conn._fobox_email_codes.insert({
            'email': data['email'],
            'code': code
        })
    await email_tools.send_verify_code(data['email'], code)
    await request.respond(HttpJSONResponse, status='ok', message=f'code has sent on {data['email']}')

@dp.post('signup')
async def signup_post(request: AsyncRequest):
    form = await request.body.form()
    if not {'name', 'email', 'code', 'password', 'repeated-password'}.issubset(set(form.keys())):
        return HttpGETRedirect(
                f'/auth/signup'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Форма не заполнена')}'
            )
    if form['password'] != form['repeated-password']:
        return HttpGETRedirect(
                f'/auth/signup'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Пароли не совпадают')}'
            )
    async with await db.acquire() as conn:
        if await conn._fobox_users.count({ 'email': form['email'] }):
            return HttpGETRedirect(
                f'/auth/signup'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Почтовый ящик уже используется')}'
            )
        if form['code'] not in [record['code'] for record in await conn._fobox_active_email_codes.find({
                'email': form['email']
            }, fields=('code', ))]:
            return HttpGETRedirect(
                f'/auth/signup'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Код подтверждения неверный')}'
            )
        await conn._fobox_email_codes.delete({
            'email': form['email'],
            'code': form['code']
        })
        token = secrets.token_urlsafe(32)
        await conn._fobox_sessions.insert({
            'token': token,
            'user_id': 
                (await conn._fobox_users.insert({
                    'name': form['name'],
                    'email': form['email'],
                    'password_hash': bcrypt.hashpw(form['password'].encode(), bcrypt.gensalt()).decode(),
                }, returning=('id', )))['id']
        })
        return HttpGETRedirect(request.args.get('redirect_uri', '/')).set_cookie(
            key='Token',
            value=token,
            expires=None if form.get('foreign_device') else datetime.datetime.now() + datetime.timedelta(weeks=2)
        )

@dp.get('restore')
async def restore(request: AsyncRequest):
    reload_components()
    with views('restore.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('View')
        await request.respond(HttpResponse, await page.html(context={
            'GET_ARGS': request.args
        }), content_type='text/html; charset=utf-8')

@dp.post('restore')
async def restore_post(request: AsyncRequest):
    form = await request.body.form()
    if 'email' not in form.keys():
        return HttpGETRedirect(
                f'/auth/restore'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Форма не заполнена')}'
            )
    async with await db.acquire() as conn:
        user = await conn._fobox_users.find_one({ 'email': form['email'] })
        if not user:
            return HttpGETRedirect(
                f'/auth/restore'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Почтовый ящик не принадлежит ни одному пользователю')}'
            )
        token = secrets.token_urlsafe(32)
        await conn._fobox_restore_tokens.insert({
            'token': token,
            'user_id': user['id'],
            'ip': request.header.get('X-Forwarded-For', request.header.get('X-Real-IP', request.ip))
        })
        await request.respond(HttpGETRedirect, f'/auth?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}')
        await email_tools.send_restore_access(form['email'], f'{app.config['link']}/{app.config['prefix']}/restore/{token}')

@dp.get('restore/<str restore_token>')
async def restore_token(request: AsyncRequest, restore_token: str):
    async with await db.acquire() as conn:
        token_record = await conn._fobox_active_restore_tokens.find_one({ 'token': restore_token })
        if not token_record:
            return 404
        if token_record['ip'] != request.header.get('X-Forwarded-For', request.header.get('X-Real-IP', request.ip)):
            return 403
    reload_components()
    with views('restore_step2.view.xml', 'r', 'utf-8') as view:
        page = gapp.new_page(view)
        page.set_entry_point('View')
        await request.respond(HttpResponse, await page.html(context={
            'GET_ARGS': request.args
        }), content_type='text/html; charset=utf-8')

@dp.post('restore/<str restore_token>')
async def restore_token_post(request: AsyncRequest, restore_token: str):
    form = await request.body.form()
    if not {'new-password', 'repeated-new-password'}.issubset(set(form.keys())):
        return HttpGETRedirect(
                f'/auth/restore/{restore_token}'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Форма не заполнена')}'
            )
    if form['new-password'] != form['repeated-new-password']:
        return HttpGETRedirect(
                f'/auth/restore/{restore_token}'
                f'?redirect_uri={urllib.parse.quote(request.args.get('redirect_uri', '/'))}'
                f'&message={urllib.parse.quote('Пароли не совпадают')}'
            )
    async with await db.acquire() as conn:
        token_record = await conn._fobox_active_restore_tokens.find_one({ 'token': restore_token })
        if not token_record:
            return 404
        if token_record['ip'] != request.header.get('X-Forwarded-For', request.header.get('X-Real-IP', request.ip)):
            return 403
        await conn._fobox_restore_tokens.delete({ 'token': restore_token })
        token = secrets.token_urlsafe(32)
        await conn._fobox_users.update(
            { 'id': token_record['user_id'] },
            { 'password_hash': bcrypt.hashpw(form['new-password'].encode(), bcrypt.gensalt()).decode() }
        )
        await conn._fobox_sessions.insert({
            'token': token,
            'user_id': token_record['user_id']
        })
        return HttpGETRedirect(request.args.get('redirect_uri', '/')).set_cookie(
            key='Token',
            value=token,
            expires=None if form.get('foreign_device') else datetime.datetime.now() + datetime.timedelta(weeks=2)
        )


dp  .static('/styles/root.css', HttpRender, 'styles/root.css', storage=views)

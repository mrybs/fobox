from slinn import ApiDispatcher, AsyncRequest, HttpResponse, ProjectAPI
from orm import get_driver_name
import json


dp = ApiDispatcher(prefix='api')
db = ProjectAPI.get_config()['dbs'][0]
match get_driver_name(db['dsn']):
    case 'postgres':
        from orm.postgres import Postgres
        db = Postgres(
            db['dsn'],
            server_settings=db['serverSettings']
        )
    case 'sqlite':
        from orm.sqlite import SQLite
        db = SQLite(
            db['dsn']
        )


@dp.get('users/<int user_id>')
async def get_user(request: AsyncRequest, user_id: int):
    async with await db.acquire() as conn:
        user = await conn._fobox_users.find_one({'id': user_id})
        if not user:
            return 404
        await request.respond(HttpResponse, json.dumps({
            'id': user_id,
            'name': user['name']
        }, ensure_ascii=False))

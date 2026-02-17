from slinn import ApiDispatcher, AsyncRequest, HttpResponse, Storage
from orm.postgres import Postgres
import geety
import config


dp = ApiDispatcher('localhost', prefix='fobox')
db = Postgres(
    config.DB_DSN,
    server_settings=config.DB_SETTINGS
)
views = Storage('fobox/views')


@dp.get()
async def index(request: AsyncRequest):
    page = geety.Page()

    with views('main.view.xml', 'r', 'utf-8') as view:
        page.load(view)

    page.set_entry_point('App')
    page.add_database_pool(db)
    
    #async with await db.acquire() as conn:
    #    print(await conn.collections())
    await request.respond(HttpResponse, await page.html(context={'users': ['mrybs', '001kpp', 'test', 'мбырс', 'чинчопа <3 <br/>']}), content_type='text/html; charset=utf-8')


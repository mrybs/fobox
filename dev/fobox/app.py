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

    with views('main.view.xml', 'r') as view:
        page.load(view)

    page.set_entry_point('App')
    
    #async with await db.acquire() as conn:
    #    print(await conn.collections())
    await request.respond(HttpResponse, page.html(), content_type='text/html')


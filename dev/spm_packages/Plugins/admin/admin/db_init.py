from orm.postgres import Postgres
from orm import get_driver_name
from slinn import ProjectAPI
import geety as G


gapp = G.App(context={
    'PNAME': ProjectAPI.get_config()['name'],
    'FOBOX_VERSION': '26.3j'
})


for db in ProjectAPI.get_config()['dbs']:
    match get_driver_name(db['dsn']):
        case 'postgres':
            gapp.add_database_pool(Postgres(
                db['dsn'],
                server_settings=db['server_settings']
            ))

fobox_db = gapp.db_pools[0]

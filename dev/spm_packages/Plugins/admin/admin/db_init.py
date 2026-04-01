from orm.postgres import Postgres
from orm import get_driver_name
from slinn import ProjectAPI
from core.version import VERSION as fobox_version
import geety as G


gapp = G.App(context={
    'PNAME': ProjectAPI.get_config()['name'],
    'FOBOX_VERSION': fobox_version['version']
})


for db in ProjectAPI.get_config()['dbs']:
    match get_driver_name(db['dsn']):
        case 'postgres':
            gapp.add_database_pool(Postgres(
                db['dsn'],
                server_settings=db['serverSettings']
            ))

fobox_db = gapp.db_pools[0]

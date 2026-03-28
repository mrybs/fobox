from abc import ABC
from slinn import Migration, ProjectAPI
from orm import get_driver_name
from orm.postgres import Postgres


class AdminBaseMigration(Migration, ABC):
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        db = ProjectAPI.get_config()['dbs'][0]
        match get_driver_name(db['dsn']):
            case 'postgres':
                self.fobox_db = Postgres(
                    db['dsn'],
                    server_settings=db['serverSettings']
                )
        self._initialized = True

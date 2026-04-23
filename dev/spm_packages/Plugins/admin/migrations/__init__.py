from abc import ABC
from slinn import Migration, ProjectAPI
from orm import get_driver_name


class AdminBaseMigration(Migration, ABC):
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        db = ProjectAPI.get_config()['dbs'][0]
        match get_driver_name(db['dsn']):
            case 'postgres':
                from orm.postgres import Postgres
                self.fobox_db = Postgres(
                    db['dsn'],
                    server_settings=db['serverSettings']
                )
            case 'sqlite':
                from orm.sqlite import SQLite
                self.fobox_db = SQLite(
                    db['dsn']
                )
        self._initialized = True

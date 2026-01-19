from __future__ import annotations
from .. import CollectionProtocol, ConnectionProtocol
from typing import Any
import asyncpg


class PostgresCollection(CollectionProtocol):
    def __init__(self, connection: PostgresConnection, name: str):
        self.connection = connection
        self.name = name

    async def find(self, _filter) -> list[dict]:
        return [dict(record) for record in await self.connection._fetch(f'''
            SELECT *
            FROM {self.name}
            {'WHERE' if _filter else ''} {' AND '.join([f'{list(_filter.keys())[i]}=${i+1}' for i in range(0, len(_filter))])};''',
            *_filter.values())]

    async def insert(self, _object) -> None: ...
    async def update(self, _filter, _object) -> None: ...
    async def delete(self, _filter) -> None: ...
    async def pop(self, _filter) -> dict: ...

class PostgresConnection(ConnectionProtocol):
    def __init__(self, pool, autocommit=True):
        self.pool = pool
        self.connection
        self.transaction
        self.autocommit = autocommit
    
    async def __aenter__(self) -> PostgresConnection:
        self.connection = await self.pool.acquire()
        self.transaction = self.connection.transaction()
        await self.transaction.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.autocommit:
            await self.commit()
        await self.pool.release(self.connection)
        del self.__dict__['connection']
        del self.__dict__['transaction']
    
    def __getattr__(self, key) -> CollectionProtocol:
        return PostgresCollection(self, key)
    
    async def commit(self) -> None:
        await self.transaction.commit()
    
    async def collections(self) -> list:
        return [collection[0] for collection in await self._fetch('''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema') AND table_type = 'BASE TABLE'
            ORDER BY table_name;''')]
    
    async def _fetch(self, query, *args, timeout: float | None = None, record_class=None) -> list:
        return await self.connection.fetch(
            query,
            *args,
            timeout=timeout,
            record_class=None
        )


async def Postgres(
        dsn: Any | None = None,
        *,
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        server_settings: dict | None = None) -> PostgresConnection:
    return PostgresConnection(
        pool=await asyncpg.create_pool(
            dsn,
            host=host,
            user=user,
            password=password,
            database=database,
            server_settings=server_settings
        )
    )

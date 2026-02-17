from __future__ import annotations
from .. import CollectionProtocol, ConnectionProtocol, PoolProtocol
from ..attributed_dict import AttributedDict
from ..typemap import typemap as tm
from typing import Any
from functools import partial
import asyncpg


class PostgresCollection(CollectionProtocol):
    def __init__(self, connection: PostgresConnection, name: str):
        self.connection = connection
        self.name = name

    async def find(
        self,
        _filter: dict,
        *,
        fields: tuple[str] = ('*',)) -> list[dict]:
        return [AttributedDict(record) for record in await self.connection._fetch(f'''
            SELECT {', '.join(fields)}
            FROM {self.name}
            {'WHERE ' if _filter else ''}{' AND '.join([f'{list(_filter.keys())[i]}=${i+1}' for i in range(0, len(_filter))])};''',
            *_filter.values())]

    async def insert(
        self,
        _object: dict,
        *,
        returning: tuple[str] = (),
        typemap: dict | None = None) -> None: 
        if not _object:
            return []
        return await self.connection._fetch(
            f'INSERT INTO {self.name}({', '.join(_object.keys())}) '
            f'VALUES({', '.join([f'${i+1}' for i in range(0, len(_object))])}) '
            f'{'RETURNING' if returning else ''} {', '.join(returning)}',
            *tm(_object, typemap).values())

    async def update(
        self,
        _filter: dict,
        _object: dict,
        *,
        returning: tuple[str] = (),
        typemap: dict | None = None) -> None:
        if not _object:
            return []
        return await self.connection._fetch(
            f'UPDATE {self.name} '
            f'SET {', '.join([f'{key}=${i+1}' for i, key in enumerate(_object)])} '
            f'{'WHERE ' if _filter else ''}{' AND '.join([f'{list(_filter.keys())[i]}=${i+len(_object)+1}' for i in range(0, len(_filter))])} '
            f'{'RETURNING' if returning else ''} {', '.join(returning)};',
            *tm(_object, typemap).values(), *_filter.values())

    async def delete(self, _filter: dict) -> None: 
        await self.connection._fetch(f'''
            DELETE FROM {self.name}
            {'WHERE ' if _filter else ''}{' AND '.join([f'{list(_filter.keys())[i]}=${i+1}' for i in range(0, len(_filter))])};''',
            *_filter.values())

    async def pop(
        self,
        _filter: dict,
        *,
        returning: tuple[str] = ('*', )) -> dict: 
        return await self.connection._fetch(
            f'DELETE FROM {self.name} '
            f'{'WHERE ' if _filter else ''}{' AND '.join([f'{list(_filter.keys())[i]}=${i+1}' for i in range(0, len(_filter))])} '
            f'{'RETURNING' if returning else ''} {', '.join(returning)};',
            *_filter.values())

    async def count(self, _filter: dict) -> int: 
        return (await self.connection._fetch(f'''
            SELECT COUNT(*)
            FROM {self.name}
            {'WHERE ' if _filter else ''}{' AND '.join([f'{list(_filter.keys())[i]}=${i+1}' for i in range(0, len(_filter))])};''',
            *_filter.values()))[0]['count']
    async def get_size(self) -> int: ...
    async def drop(self) -> None: ...


class PostgresConnection(ConnectionProtocol):
    def __init__(self, pool, connection, transaction, autocommit=True):
        self._pool = pool
        self._connection = connection
        self._transaction = transaction
        self._autocommit = autocommit
    
    def __getattr__(self, key) -> CollectionProtocol:
        return PostgresCollection(self, key)
    
    async def rollback(self) -> None:
        await self._transaction.rollback()
    
    async def commit(self) -> None:
        await self._transaction.commit()
    
    async def collections(self) -> list:
        return [collection[0] for collection in await self._fetch('''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema') AND table_type = 'BASE TABLE'
            ORDER BY table_name;''')]
    
    async def __aenter__(self):
        await self._transaction.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if not exc_type and self._autocommit:
                await self.commit()
            else:
                await self.rollback()
        finally:
            await self._pool.release(self)
    
    async def _fetch(self, query, *args, timeout: float | None = None, record_class=None) -> list:
        query = ' '.join([line.strip() for line in query.split('\n')]).strip()
        return await self._connection.fetch(
            query,
            *args,
            timeout=timeout,
            record_class=record_class
        )

class PostgresPool(PoolProtocol):
    def __init__(self, pool_factory, autocommit=True):
        self._pool_factory = pool_factory
        self._autocommit = autocommit
        self._pool = None
    
    async def connect(self):
        self._pool = await self._pool_factory()
    
    async def acquire(self) -> PostgresConnection:
        if not self._pool:
            await self.connect()
        connection = await self._pool.acquire()
        transaction = connection.transaction()
        return PostgresConnection(self, connection, transaction)
    
    async def release(self, connection: PostgresConnection):
        await self._pool.release(connection._connection)
        del connection


def Postgres(
        dsn: Any | None = None,
        *,
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        server_settings: dict | None = None,
        autocommit: bool = True) -> PostgresPool:
    return PostgresPool(
        partial(
            asyncpg.create_pool,
            dsn,
            host=host,
            user=user,
            password=password,
            database=database,
            server_settings=server_settings
        ),
        autocommit=autocommit
    )

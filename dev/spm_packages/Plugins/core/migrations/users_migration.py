from . import CoreBaseMigration


class UsersMigration(CoreBaseMigration):
    @property
    def dependencies(self) -> tuple[str, ...]:
        return (
            'RolesMigration.core',
        )

    async def check(self) -> bool:
        if hasattr(self, '_applied'):
            return False
        async with await self.fobox_db.acquire() as conn:
            return '_fobox_users' not in await conn.collections()

    async def apply(self):
        async def _apply_postgres(conn):
            await conn._fetch(
                """
                    CREATE TABLE IF NOT EXISTS _fobox_users(
                        id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        role INT NOT NULL DEFAULT 1 REFERENCES _fobox_roles(code),
                        registered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """
            )
            await conn._fetch(
                """
                    CREATE UNIQUE INDEX IF NOT EXISTS _fobox_users_emails
                    ON _fobox_users (email);
                """
            )
        
        async def _apply_sqlite(conn):
            await conn._fetch(
                """
                CREATE TABLE IF NOT EXISTS _fobox_users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role INTEGER NOT NULL DEFAULT 1 REFERENCES _fobox_roles(code),
                    registered_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            await conn._fetch(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS _fobox_users_emails
                ON _fobox_users (email)
                """
            )

        async with await self.fobox_db.acquire() as conn:
            if type(conn).__name__ == 'PostgresConnection':
                await _apply_postgres(conn)
            elif type(conn).__name__ == 'SQLiteConnection':
                await _apply_sqlite(conn)
            
        await self.fobox_db.close()
        self._applied = True

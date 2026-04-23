from . import CoreBaseMigration


class RestoreTokensMigration(CoreBaseMigration):
    @property
    def dependencies(self) -> tuple[str, ...]:
        return (
            'UsersMigration.core',
        )

    async def check(self) -> bool:
        async with await self.fobox_db.acquire() as conn:
            return '_fobox_restore_tokens' not in await conn.collections()

    async def apply(self):
        async def _apply_postgres(conn):
            await conn._fetch(
                """
                    CREATE TABLE IF NOT EXISTS _fobox_restore_tokens(
                        token TEXT PRIMARY KEY,
                        user_id INT NOT NULL REFERENCES _fobox_users(id),
                        ip TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 minutes')
                    );
                """
            )
            await conn._fetch(
                """
                    CREATE OR REPLACE VIEW _fobox_active_restore_tokens AS
                    SELECT * FROM _fobox_restore_tokens WHERE expires_at >= NOW();
                """
            )
            await conn._fetch(
                """
                    DELETE FROM _fobox_restore_tokens WHERE ctid IN (
                        SELECT ctid FROM _fobox_restore_tokens WHERE expires_at < NOW() LIMIT 1000
                    );
                """
            )

        async def _apply_sqlite(conn):
            await conn._fetch(
                """
                CREATE TABLE IF NOT EXISTS _fobox_restore_tokens(
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES _fobox_users(id),
                    ip TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    expires_at TEXT NOT NULL DEFAULT (datetime('now', '+30 minutes'))
                )
                """
            )
            # Представление активных токенов
            await conn._fetch(
                """
                CREATE VIEW IF NOT EXISTS _fobox_active_restore_tokens AS
                SELECT * FROM _fobox_restore_tokens WHERE expires_at >= datetime('now')
                """
            )
            # Удаление просроченных токенов (одноразовая очистка при миграции)
            await conn._fetch(
                """
                DELETE FROM _fobox_restore_tokens
                WHERE expires_at < datetime('now')
                """
            )

        async with await self.fobox_db.acquire() as conn:
            if type(conn).__name__ == 'PostgresConnection':
                await _apply_postgres(conn)
            elif type(conn).__name__ == 'SQLiteConnection':
                await _apply_sqlite(conn)
        await self.fobox_db.close()

from . import CoreBaseMigration


class EmailCodesMigration(CoreBaseMigration):
    async def check(self) -> bool:
        async with await self.fobox_db.acquire() as conn:
            return '_fobox_email_codes' not in await conn.collections()

    async def apply(self):
        async def _apply_postgres(conn):
            await conn._fetch(
                """
                    CREATE TABLE IF NOT EXISTS _fobox_email_codes(
                        email TEXT NOT NULL,
                        code TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '5 minutes')
                    )
                """
            )
            await conn._fetch(
                """
                    CREATE INDEX IF NOT EXISTS _fobox_email_codes_emails
                    ON _fobox_email_codes (email);
                """
            )
            await conn._fetch(
                """
                    CREATE OR REPLACE VIEW _fobox_active_email_codes AS
                    SELECT * FROM _fobox_email_codes WHERE expires_at >= NOW();
                """
            )
            await conn._fetch(
                """
                    DELETE FROM _fobox_email_codes WHERE ctid IN (
                        SELECT ctid FROM _fobox_email_codes WHERE expires_at < NOW() LIMIT 1000
                    );
                """
            )
        async def _apply_sqlite(conn):
            await conn._fetch(
                """
                CREATE TABLE IF NOT EXISTS _fobox_email_codes(
                    email TEXT NOT NULL,
                    code TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    expires_at TEXT NOT NULL DEFAULT (datetime('now', '+5 minutes'))
                )
                """
            )
            await conn._fetch(
                """
                CREATE INDEX IF NOT EXISTS _fobox_email_codes_emails
                ON _fobox_email_codes (email)
                """
            )
            await conn._fetch(
                """
                CREATE VIEW IF NOT EXISTS _fobox_active_email_codes AS
                SELECT * FROM _fobox_email_codes
                WHERE expires_at >= datetime('now')
                """
            )
            await conn._fetch(
                """
                DELETE FROM _fobox_email_codes
                WHERE expires_at < datetime('now')
                """
            )
        async with await self.fobox_db.acquire() as conn:
            if type(conn).__name__ == 'PostgresConnection':
                await _apply_postgres(conn)
            elif type(conn).__name__ == 'SQLiteConnection':
                await _apply_sqlite(conn)
        
        await self.fobox_db.close()

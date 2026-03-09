from . import AdminBaseMigration


class EmailCodesMigration(AdminBaseMigration):
    async def check(self) -> bool:
        return True

    async def apply(self):
        async with await self.fobox_db.acquire() as conn:
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
        await self.fobox_db._pool.close()

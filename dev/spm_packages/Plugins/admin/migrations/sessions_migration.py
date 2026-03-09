from . import AdminBaseMigration


class SessionsMigration(AdminBaseMigration):
    @property
    def dependencies(self) -> tuple[str, ...]:
        return (
            'UsersMigration.admin',
        )

    async def check(self) -> bool:
        return True

    async def apply(self):
        async with await self.fobox_db.acquire() as conn:
            await conn._fetch(
                """
                    CREATE TABLE IF NOT EXISTS _fobox_sessions(
                        token TEXT PRIMARY KEY,
                        user_id INT NOT NULL REFERENCES _fobox_users(id),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '2 weeks')
                    );
                """
            )
            await conn._fetch(
                """
                    CREATE OR REPLACE VIEW _fobox_active_sessions AS
                    SELECT * FROM _fobox_sessions WHERE expires_at >= NOW();
                """
            )
            await conn._fetch(
                """
                    DELETE FROM _fobox_sessions WHERE ctid IN (
                        SELECT ctid FROM _fobox_sessions WHERE expires_at < NOW() LIMIT 1000
                    );
                """
            )
        await self.fobox_db._pool.close()

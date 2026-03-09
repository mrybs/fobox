from . import AdminBaseMigration


class UsersMigration(AdminBaseMigration):
    @property
    def dependencies(self) -> tuple[str, ...]:
        return (
            'RolesMigration.admin',
        )

    async def check(self) -> bool:
        if hasattr(self, '_applied'):
            return False
        async with await self.fobox_db.acquire() as conn:
            return '_fobox_users' in await conn.collections()

    async def apply(self):
        async with await self.fobox_db.acquire() as conn:
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
        await self.fobox_db._pool.close()
        self._applied = True

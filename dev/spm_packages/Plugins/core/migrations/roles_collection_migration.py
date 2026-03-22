from . import CoreBaseMigration


class RolesCollectionMigration(CoreBaseMigration):
    async def check(self) -> bool:
        async with await self.fobox_db.acquire() as conn:
            return '_fobox_roles' not in await conn.collections()

    async def apply(self):
        async with await self.fobox_db.acquire() as conn:
            await conn._fetch(
                """
                    CREATE TABLE IF NOT EXISTS _fobox_roles(
                        code INT PRIMARY KEY,
                        name TEXT NOT NULL,
                        display_name TEXT NOT NULL
                    );
                """
            )
        await self.fobox_db._pool.close()
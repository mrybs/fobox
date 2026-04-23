from . import CoreBaseMigration


class PagesCollectionMigration(CoreBaseMigration):
    async def check(self) -> bool:
        async with await self.fobox_db.acquire() as conn:
            return '_fobox_pages' not in await conn.collections()

    async def apply(self):
        async with await self.fobox_db.acquire() as conn:
            await conn._fetch(
                """
                    CREATE TABLE IF NOT EXISTS _fobox_pages(
                        path TEXT PRIMARY KEY,
                        creator_id INT NOT NULL REFERENCES _fobox_users(id),
                        enabled BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """
            )
        await self.fobox_db.close()
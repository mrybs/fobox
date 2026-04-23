from . import CoreBaseMigration


class RolesMigration(CoreBaseMigration):
    @property
    def dependencies(self) -> tuple[str, ...]:
        return (
            'RolesCollectionMigration.core',
        )

    async def check(self) -> bool:
        async with await self.fobox_db.acquire() as conn:
            return not (
                await conn._fobox_roles.count({'code': 0}) or
                await conn._fobox_roles.count({'code': 1}) or
                await conn._fobox_roles.count({'code': 2})
            )

    async def apply(self):
        async with await self.fobox_db.acquire() as conn:
            await conn._fobox_roles.insert({
                'code': 0,
                'name': 'guest',
                'display_name': 'Гость'
            })
            await conn._fobox_roles.insert({
                'code': 1,
                'name': 'user',
                'display_name': 'Пользователь'
            })
            await conn._fobox_roles.insert({
                'code': 2,
                'name': 'admin',
                'display_name': 'Администратор'
            })
        await self.fobox_db.close()
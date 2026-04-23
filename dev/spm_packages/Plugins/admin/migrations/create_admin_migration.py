from . import AdminBaseMigration
from core.email_tools import send_verify_code
import secrets
import string
import getpass
import bcrypt


class CreateAdminMigration(AdminBaseMigration):
    @property
    def dependencies(self) -> tuple[str, ...]:
        return (
            'UsersMigration.core',
        )

    async def check(self) -> bool:
        async with await self.fobox_db.acquire() as conn:
            return not await conn._fobox_users.count({'role': 2})

    async def apply(self):
        print('\033[94mНет ни одной администраторской учетной записи\033[0m')
        name = input('Введите имя: ')
        email = input('Введите email: ')
        code = ''.join([secrets.choice(string.digits) for _ in range(6)])
        await send_verify_code(email, code)
        while code != input('Введите код подтверждения: F-'):
            print('Код неверный')
        password = getpass.getpass('Введите пароль: ')
        while password != getpass.getpass('Повторите пароль: '):
            print('\033[91mПароли не совпадают\033[0m')
            password = getpass.getpass('Введите пароль: ')
        async with await self.fobox_db.acquire() as conn:
            user_id = await conn._fobox_users.insert({
                'name': name,
                'email': email,
                'password_hash': bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
                'role': 2
            }, returning=('id',))
            print(f'\033[92mУчетная запись \033[1m#{user_id["id"]}\033[22m создана\033[0m')
        await self.fobox_db.close()
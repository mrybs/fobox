from slinn import Migration, ProjectAPI
import getpass


class ConfigMigration(Migration):
    async def check(self) -> bool:
        return ProjectAPI.get_config().get('configMigrationRequired', True)

    async def apply(self):
        print('Запущен мастер первичной настройки (CTRL+C для выхода)')
        name = input('Имя вашего проекта(на английском): ')
        print('Настройка основной базы данных')
        dsn = input('DSN основной БД: ')
        scheme = input('Схема основной БД: ')
        print('Настройка электронной почты')
        smtp_host = input('Хост почтового SMTP сервера: ')
        smtp_address = input('Адрес электронной почты: ')
        smtp_password = getpass.getpass('Пароль от электронной почты: ')
        ProjectAPI.update_config({
            'name': name,
            'dbs': [
                {
                    'dsn': dsn,
                    'server_settings': {
                        'search_path': scheme
                    }
                }
            ],
            'smtp': {
                'server_host': smtp_host,
                'server_port': 587,
                'address': smtp_address,
                'password': smtp_password
            }
        })

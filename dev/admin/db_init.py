from orm.postgres import Postgres
from orm import get_driver_name, ConnectionProtocol
from slinn_api import SlinnAPI
from email_tools import send_verify_code
import secrets
import string
import geety as G
import bcrypt
import getpass


gapp = G.App(context={
    'PNAME': SlinnAPI.get_config()['name']
})


for db in SlinnAPI.get_config()['dbs']:
    match get_driver_name(db['dsn']):
        case 'postgres':
            gapp.add_database_pool(Postgres(
                db['dsn'],
                server_settings=db['server_settings']
            ))

fobox_db = gapp.db_pools[0]

async def db_init(conn: ConnectionProtocol):
    # TODO: replace with crossbase implementation
    await conn._fetch(
    """
    CREATE TABLE IF NOT EXISTS _fobox_roles(
        code INT PRIMARY KEY,
        name TEXT NOT NULL,
        display_name TEXT NOT NULL
    );
    """)
    if not await conn._fobox_roles.count({'code': 0}):
        await conn._fobox_roles.insert({
            'code': 0,
            'name': 'guest',
            'display_name': 'Гость'
        })
    if not await conn._fobox_roles.count({'code': 1}):
        await conn._fobox_roles.insert({
            'code': 1,
            'name': 'user',
            'display_name': 'Пользователь'
        })
    if not await conn._fobox_roles.count({'code': 2}):
        await conn._fobox_roles.insert({
            'code': 2,
            'name': 'admin',
            'display_name': 'Администратор'
        })
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
    """)
    await conn._fetch(
    """
    CREATE UNIQUE INDEX IF NOT EXISTS _fobox_users_emails
    ON _fobox_users (email);
    """)
    await conn._fetch(
    """
    CREATE TABLE IF NOT EXISTS _fobox_sessions(
        token TEXT PRIMARY KEY,
        user_id INT NOT NULL REFERENCES _fobox_users(id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '2 weeks')
    );
    """)
    await conn._fetch(
    """
    CREATE OR REPLACE VIEW _fobox_active_sessions AS
    SELECT * FROM _fobox_sessions WHERE expires_at >= NOW();
    """)
    await conn._fetch(
    """
    DELETE FROM _fobox_sessions WHERE ctid IN (
        SELECT ctid FROM _fobox_sessions WHERE expires_at < NOW() LIMIT 1000
    );
    """)
    await conn._fetch(
    """
    CREATE TABLE IF NOT EXISTS _fobox_email_codes(
        email TEXT NOT NULL,
        code TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '5 minutes')
    )
    """)
    await conn._fetch(
    """
    CREATE INDEX IF NOT EXISTS _fobox_email_codes_emails
    ON _fobox_email_codes (email);
    """)
    await conn._fetch(
    """
    CREATE OR REPLACE VIEW _fobox_active_email_codes AS
    SELECT * FROM _fobox_email_codes WHERE expires_at >= NOW();
    """)
    await conn._fetch(
    """
    DELETE FROM _fobox_email_codes WHERE ctid IN (
        SELECT ctid FROM _fobox_email_codes WHERE expires_at < NOW() LIMIT 1000
    );
    """)
    await conn._fetch(
    """
    CREATE TABLE IF NOT EXISTS _fobox_restore_tokens(
        token TEXT PRIMARY KEY,
        user_id INT NOT NULL REFERENCES _fobox_users(id),
        ip TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 minutes')
    );
    """)
    await conn._fetch(
    """
    CREATE OR REPLACE VIEW _fobox_active_restore_tokens AS
    SELECT * FROM _fobox_restore_tokens WHERE expires_at >= NOW();
    """)
    await conn._fetch(
    """
    DELETE FROM _fobox_restore_tokens WHERE ctid IN (
        SELECT ctid FROM _fobox_restore_tokens WHERE expires_at < NOW() LIMIT 1000
    );
    """)
    if not await conn._fobox_users.count({'role': 2}):
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
        user_id = await conn._fobox_users.insert({
            'name': name,
            'email': email,
            'password_hash': bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            'role': 2
        }, returning=('id', ))
        print(f'\033[92mУчетная запись \033[1m#{user_id['id']}\033[22m создана\033[0m')


fobox_db.on_acquire(db_init)

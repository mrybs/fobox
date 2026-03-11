<h1 align="center">Фобокс</h1>
<h3 align="center">Конструктор сайтов</h3>
<div align="center">
    <img src="https://img.shields.io/github/license/openmiot/fobox"/>
    <img src="https://img.shields.io/badge/Python-3.14-red">
    <img src="https://img.shields.io/badge/Running_on-Slinn2-%23FF00EE">
    <img src="https://img.shields.io/github/languages/code-size/openmiot/fobox">
    <img src="https://img.shields.io/github/issues/openmiot/fobox?color=%23eeaa00">
</div>

<p>
    <b>Фобокс</b> — автономный конструктор сайтов на стеке <a href="https://github.com/OpenMiot">Miot</a>
<p>

### Возможности
- Визуальный редактор
- Поддержка сторонних плагинов
- Система авторизации
<!-- - ИИ-помощник -->

## Установка
### Необходимые зависимости
Для работы конструктора на ПК или сервер установите:
- Python 3.14 и выше
- PostgreSQL
- Git
- Curl

Откройте командную строку Windows, введите:
```sh
# Установка пакета с HTTP-фреймворком
pip install git+https://github.com/OpenMiot/slinn@nukeful

slinn create www  # вместо www название папки с проектом
cd www
venv/Scripts/activate

# Установка пакета с языком Geety и ORM, а также пакета для хеширования паролей
py -m pip install geety[postgres] bcrypt

# Установка основных плагинов конструктора 
# Здесь при запросе необходимо нажать Enter
spm update
spm install core@fobox.core auth@fobox.core admin@fobox.core fobox_app@fobox.core
slinn template fobox_app app

curl -OJ https://raw.githubusercontent.com/OpenMiot/fobox/refs/heads/main/dev/project.json.example
move project.json.example project.json

explorer .
```
В открывшемся окне проводника будет файл project.json. Измените его (например, через блокнот). 

В части файла, указанной ниже, замените `postgres` на пользователя PostgreSQL и `1234` на его пароль (пользователь и пароль задаются при установке PostgreSQL)
```json
"dbs": [
    {
        "dsn": "postgres://postgres:1234@localhost/postgres",
        "server_settings": {
            "search_path": "public"
        }
    }
]
```
В части файла, указанной ниже, замените:
- `smtp.gmail.com` на SMTP сервер вашего почтового клиента
- `example@gmail.com` на ваш адрес электронной почты
- `abcd efgh jklm nopq` на пароль 
- `587` — порт SMTP сервера, но его скорее всего менять не требуется

```json
"smtp": {
    "server_host": "smtp.gmail.com",
    "server_port": 587,
    "address": "example@gmail.com",
    "password": "abcd efgh jklm nopq"
}
```
Соответвующие данные можно узнать у почтового сервиса. (используйте поисковик Google или Яндекс)

После внесения необходимых изменений, введите в командную строку Windows:
```sh
# Применение миграций
slinn makemigrations
```
Эта команда попросит создать учетную запись администратора, следуйте инструкциям

## Запуск
Теперь, когда сайт установлен, его нужно запустить. В папке с сервером запустите файл `start.bat` для Windows

> [!IMPORTANT]
> Для работы сайта необходима запущенная консоль

<p align="center">
    <img src="docs/images/start-bat.png" width="600px"/>
</p>

Сайт будет доступен по ссылке, выведенной в консоль, обычно это http://localhost:8080.

<p align="center">
    <img src="docs/images/greetings.png" width="600px"/>
</p>

Для дальнейшей настройки необходимо открыть панель управления по ссылке на главной странице или через http://localhost:8080/fobox. Перед этим вас попросит войти в учетную запись. Входите в учетную запись администратора, которого создали ранее

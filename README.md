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

Откройте командную строку Windows, введите:
```sh
# Установка пакета с HTTP-фреймворком
pip install git+https://github.com/OpenMiot/slinn@nukeful

slinn-admin create-project www  # вместо www название папки с проектом
cd www
venv/Scripts/activate

# Установка пакета с языком Geety и ORM, а также пакета для хеширования паролей
pip install geety[postgres] bcrypt

# Установка основных плагинов конструктора 
# Здесь при запросе необходимо нажать Enter
spm update
spm install core@fobox.core auth@fobox.core admin@fobox.core fobox-app@fobox.core
slinn template fobox-app app

# Применение миграций
slinn migrate-all
```
Последняя команда вас попросит указать данные для подключения к БД, к почтовому сервису и создаст учетную запись администратора, следуйте инструкциям

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

Для дальнейшей настройки необходимо открыть панель управления по ссылке на главной странице или через http://localhost:8080/fobox. Перед этим необходимо войти в учетную запись. Входите в учетную запись администратора, которого создали ранее, через http://localhost:8080/auth

> [!IMPORTANT]
> Вас не пустит в панель управления сайтом, если вы не вошли в учетную запись администратора

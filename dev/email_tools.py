import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slinn_api import SlinnAPI


CONFIG = SlinnAPI.get_config()


def _send_email(
        sender_server_hostname,
        sender_server_port,
        sender_email,
        sender_password,
        receiver_email,
        subject,
        body):
    message = MIMEMultipart()
    message['From'] = f'Fobox Конструктор сайтов <{sender_email}>'
    message['To'] = receiver_email
    message['Subject'] = subject
    message['Reply-To'] = sender_email
    message['Content-Type'] = "text/html; charset=utf-8"
    message['Content-Language'] = "ru-RU"
    #message['List-Unsubscribe'] = "<>"

    message.attach(MIMEText(body, "html", "utf-8"))

    with smtplib.SMTP(sender_server_hostname, sender_server_port) as server:
        server.starttls()  # Шифрование TLS
        server.login(sender_email, sender_password)
        server.sendmail(
            sender_email, 
            receiver_email, 
            message.as_string()
        )

async def send_email(receiver_email, subject, body):
    await asyncio.get_event_loop().run_in_executor(
        None,
        _send_email,
        CONFIG['smtp']['server_host'],
        CONFIG['smtp']['server_port'],
        CONFIG['smtp']['address'],
        CONFIG['smtp']['password'],
        receiver_email,
        subject,
        body
    )

async def send_verify_code(receiver_email, code):
    await send_email(
        receiver_email,
        'Подтвердите вход',
        f'<html lang="ru"><h3>Код подтверждения входа в аккаунт:</h3><h1><b style="color:#e03318">F-{code}</b></h1></html>'
    )

async def send_restore_access(receiver_email, link):
    await send_email(
        receiver_email,
        'Восстановление доступа',
        f'<html lang="ru"><h3>Для восстановления доступа к аккаунту перейдите по ссылке ниже</h3><a href="{link}">{link}</a></html>'
    )

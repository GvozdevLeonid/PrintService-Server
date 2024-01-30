"""
Celery config for app project.
"""
from django.conf import settings
from celery import Celery
import imaplib
import email
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery('app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check_new_email_files_every_10_minutes': {
        'task': 'app.celery.check_new_files',
        'schedule': 60 * 10.0,
    },
}


@app.task
def check_new_files():
    from core import models
    imap = imaplib.IMAP4_SSL(host=settings.EMAIL['host'], port=settings.EMAIL['port'])
    imap.login(settings.EMAIL['adress'], settings.EMAIL['password'])
    imap.select("inbox")

    status, message_ids = imap.uid('search', None, 'UNSEEN')
    if status == 'OK':
        message_ids = message_ids[0].split()
        message_ids = [message_id.decode() for message_id in message_ids]

        for message_id in message_ids:
            file_names = []
            imap.uid('STORE', message_id, '+FLAGS', '(\SEEN)')  # NOQA W605
            result, message_data = imap.uid('fetch', message_id, '(BODY.PEEK[])')
            raw_email = message_data[0][1].decode('utf-8')
            email_message = email.message_from_string(raw_email)

            username, user_email = email.utils.parseaddr(email_message['From'])

            if email_message.get_content_maintype() == 'multipart':
                for part in email_message.get_payload():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    filename, encoding = email.header.decode_header(part.get_filename())[0]
                    if encoding is not None:
                        file_name = filename.decode(encoding)
                    file_names.append(file_name)

            if len(file_names):
                models.EmailMessage.objects.create(
                    email=user_email,
                    message_id=message_id,
                    file_names='<|||>'.join(file_names)
                ).save()

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from celery import shared_task
import imaplib
import email
import time
import json
import io


def calculate_print_cost(print_settings: str, kiosk_id: int) -> float:
    from core import models
    kiosk_object = models.Kiosk.objects.get(id=kiosk_id)
    print_settings = json.loads(print_settings)

    price_objects = models.Price.objects.filter(kiosk=kiosk_object, print_settings=print_settings['print_settings'], start_page__lte=print_settings['total_pages']).order_by('start_page')
    for price_object in price_objects:
        if price_object.end_page is None or price_object.end_page >= print_settings['total_pages']:
            return print_settings['total_pages'] * price_object.price


def get_next_guest_identificator() -> str:
    from core import models

    def increment_letters(letters):
        reversed_letters = letters[::-1]
        for i, letter in enumerate(reversed_letters):
            if letter < 'Z':
                new_letters = reversed_letters[:i] + chr(ord(letter) + 1) + reversed_letters[i + 1:]
                return new_letters[::-1]
        return 'A' * settings.IDENTIFICATOR["letters"]

    last_print = models.Print.objects.filter(user__phone_number=settings.GUEST['phone_number']).order_by('-id').first()
    if not last_print:
        return f'{"A" * settings.IDENTIFICATOR["letters"]}{"0" * settings.IDENTIFICATOR["numbers"]}'
    else:
        identificator = last_print.identificator

    letters = identificator[:settings.IDENTIFICATOR['letters']]
    numbers = int(identificator[settings.IDENTIFICATOR['letters']:])

    if numbers < (10**settings.IDENTIFICATOR['numbers']) - 1:
        numbers += 1
    else:
        numbers = 0
        letters = increment_letters(letters)

    return letters + str(numbers).zfill(settings.IDENTIFICATOR['numbers'])


@shared_task
def check_print_queue(channel_name: str, last_id: int) -> None:
    from core import models
    if last_id is not None:
        while True:
            if models.Print.objects.all().last().id > last_id:
                break
            else:
                time.sleep(1)

    async_to_sync(get_channel_layer().send)(
        channel_name,
        {
            'type': 'chat_message',
            'action': 'check_print_queue',
            'last_id': models.Print.objects.all().last().id
        }
    )


@shared_task
def check_transactions(channel_name: str, last_id: int) -> None:
    from core import models
    if last_id is not None:
        while True:
            if models.Transaction.objects.all().last().id > last_id:
                break
            else:
                time.sleep(1)

    async_to_sync(get_channel_layer().send)(
        channel_name,
        {
            'type': 'chat_message',
            'action': 'check_transactions',
            'last_id': models.Transaction.objects.all().last().id
        }
    )


def parse_configured_printers(configured_printers: dict) -> list[str]:
    price_list = []

    def parse(obj, keys=[]):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    continue
                if isinstance(v, dict):
                    parse(v, keys + [k])
                else:
                    price_list.append(' / '.join(keys + [k]))

    parse(configured_printers)

    return price_list


def create_price_list(price_list: list[str], kiosk) -> None:
    from core import models
    models.Price.objects.filter(kiosk=kiosk).delete()
    for price in price_list:
        models.Price.objects.create(
            print_settings=price,
            start_page=1,
            price=0.00,
            kiosk=kiosk
        ).save()


def create_print(phone_number, print_settings, kiosk_key) -> dict:
    from core import models
    user_object = models.User.objects.get(phone_number=phone_number)
    kiosk_object = models.Kiosk.objects.get(key=kiosk_key)

    print_cost = calculate_print_cost(print_settings, kiosk_object.id)

    if user_object.phone_number == settings.GUEST['phone_number']:

        print_object = models.Print.objects.create(
            print_settings=print_settings,
            identificator=get_next_guest_identificator(),
            status='await',
            kiosk=kiosk_object,
            user=user_object
        )

        if user_object.allow_credit:
            transaction = models.Transaction.objects.create(
                identificator=print_object.identificator,
                amount=print_cost,
                type='guest print',
                user=user_object,
                confirming_user=user_object
            )
            transaction.save()

            print_object.transaction = transaction
            print_object.status = 'printed'

        print_object.save()

        return {'status': 'ok', 'print': True if user_object.allow_credit else False, 'print_id': print_object.id, 'identificator': print_object.identificator}

    elif user_object.balance < print_cost and not user_object.allow_credit:
        print_object = models.Print.objects.create(
            print_settings=print_settings,
            identificator=user_object.phone_number,
            status='await',
            kiosk=kiosk_object,
            user=user_object
        )
        print_object.save()

        return {'status': 'ok', 'print': False, 'print_id': print_object.id, 'identificator': print_object.identificator}

    elif user_object.balance >= print_cost or user_object.allow_credit:

        transaction = models.Transaction.objects.create(
            identificator=user_object.phone_number,
            amount=print_cost,
            type='withdrawal',
            user=user_object,
            confirming_user=user_object
        )
        transaction.save()

        print_object = models.Print.objects.create(
            print_settings=print_settings,
            identificator=user_object.phone_number,
            status='printed',
            kiosk=kiosk_object,
            user=user_object,
            transaction=transaction
        )
        print_object.save()

        user_object.balance -= print_cost
        user_object.save()

        return {'status': 'ok', 'print': True, 'print_id': print_object.id, 'identificator': print_object.identificator}


def get_file_from_email(message_id, selected_file_name):
    imap = imaplib.IMAP4_SSL(host=settings.EMAIL['host'], port=settings.EMAIL['port'])
    imap.login(settings.EMAIL['adress'], settings.EMAIL['password'])
    imap.select("inbox")

    status, message_ids = imap.uid('search', None, 'UNSEEN')
    if status == 'OK':
        imap.uid('STORE', message_id, '+FLAGS', '(\SEEN)')
        result, message_data = imap.uid('fetch', message_id, '(BODY.PEEK[])')
        raw_email = message_data[0][1].decode('utf-8')
        email_message = email.message_from_string(raw_email)

        if email_message.get_content_maintype() == 'multipart':
            for part in email_message.get_payload():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                filename, encoding = email.header.decode_header(part.get_filename())[0]
                if encoding is not None:
                    file_name = filename.decode(encoding)

                if selected_file_name == file_name:
                    return io.BytesIO(part.get_payload(decode=True))

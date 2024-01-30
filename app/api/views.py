from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from api import functions
from core import models
import json
import os


@csrf_exempt
def add_kiosk(request, key):
    if request.method == 'POST':
        if (models.Kiosk.objects.filter(key=key).exists()):
            kiosk = models.Kiosk.objects.get(key=key)
            configured_printers = request.POST.get('configured_printers', '')
            if configured_printers != '':
                kiosk.configured_printers = configured_printers
                kiosk.status = 'active'
                kiosk.save()

                price_list = functions.parse_configured_printers(json.loads((configured_printers)))
                functions.create_price_list(price_list, kiosk)

            return JsonResponse({'status': 'ok', 'added': True})

    return Http404()


@csrf_exempt
def check_user(request, key):
    if request.method == 'POST':
        if (models.Kiosk.objects.filter(key=key).exists()):
            phone_number = request.POST.get('phone_number')
            password = request.POST.get('password')

            if models.User.objects.filter(phone_number=phone_number).exists():
                user = models.User.objects.get(phone_number=phone_number)
                if user.check_password(password):
                    return JsonResponse({'status': 'ok', 'user': {'phone_number': user.phone_number, 'balance': user.balance, 'email': user.email, 'name': user.name}})

    return JsonResponse({'status': 'bad'})


@csrf_exempt
def new_print(request, key):
    if request.method == 'POST':
        if (models.Kiosk.objects.filter(key=key).exists()):
            user_phone_number = request.POST.get('phone_number')
            print_settings = request.POST.get('print_settings')

            response = functions.create_print(user_phone_number, print_settings, key)

            return JsonResponse(response)

    return Http404()


@csrf_exempt
def check_print(request, key):
    if request.method == 'POST':
        if (models.Kiosk.objects.filter(key=key).exists()):
            print_id = request.POST.get('print_id')
            print_object = models.Print.objects.get(id=print_id)
            return JsonResponse({'status': print_object.status})
    return JsonResponse({'status': 'await'})


@csrf_exempt
def email_files_list(request, key):
    if request.method == 'POST':
        if (models.Kiosk.objects.filter(key=key).exists()):
            user_phone_number = request.POST.get('phone_number')
            email = request.POST.get('email')
            file_names = []
            if not models.User.objects.filter(email=email).exists():
                email_message_objects = models.EmailMessage.objects.filter(email=email)
                for email_message in email_message_objects:
                    email_message_file_names = email_message.file_names.split('<|||>')
                    for email_message_file_name in email_message_file_names:
                        if email_message_file_name != '':
                            file_names.append([email_message.message_id, email_message_file_name])

            else:
                if models.User.objects.filter(email=email, phone_number=user_phone_number).exists():
                    email_message_objects = models.EmailMessage.objects.filter(email=email)
                    for email_message in email_message_objects:
                        email_message_file_names = email_message.file_names.split('<|||>')
                        for email_message_file_name in email_message_file_names:
                            if email_message_file_name != '':
                                file_names.append([email_message.message_id, email_message_file_name])

            return JsonResponse({'status': 'ok', 'file_names': file_names.__str__()})

    return Http404()


@csrf_exempt
def download_file_from_email(request, key):
    if request.method == 'POST':
        if (models.Kiosk.objects.filter(key=key).exists()):
            message_id = request.POST.get('message_id')
            file_name = request.POST.get('file_name')

            ext = os.path.splitext(file_name)[1]

        response = FileResponse(functions.get_file_from_email(message_id, file_name), content_type=f'application/{ext}')
        response['Content-Disposition'] = f'attachment; filename="{message_id}_{file_name}"'

        return response

    return Http404()


@csrf_exempt
def kiosk_status(request, key):
    if request.method == 'POST':
        if (models.Kiosk.objects.filter(key=key).exists()):
            if request.POST.get('get_status', '') != '':
                return JsonResponse({'status': models.Kiosk.objects.get(key=key).status})
            elif request.POST.get('set_status', '') != '':
                kiosk_object = models.Kiosk.objects.get(key=key)
                kiosk_object.status = request.POST.get('set_status')
                kiosk_object.save()
                return JsonResponse({'status': 'ok'})

    return Http404()

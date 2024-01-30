from django.db.models import Case, When, Value, IntegerField, Q, Sum
from django.shortcuts import render, HttpResponse, redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from django.conf import settings
from core import models, forms
from api import functions
import uuid
import json


def print_queue(request):
    if request.user.is_staff:
        context = {'dashboard_page': 'print_queue', 'username': request.user.name}
        return render(request, template_name='dashboard/print_queue/print_queue.html', context=context)

    return redirect('login')


def print_queue_table(request):
    if request.user.is_staff and request.method == 'POST':
        table = [

            {'row': [{'text': _('Kiosk')},
                     {'text': _('Identificator')},
                     {'text': _('Date')},
                     {'text': _('Amount')},
                     {'text': _('Status')}]},
        ]
        search_input = request.POST.get('search-input')
        page_number = int(request.POST.get('page_number', 1))

        print_objects = models.Print.objects.annotate(
            custom_order=Case(
                When(status='await', then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        )

        if search_input != '':
            print_objects = print_objects.filter(identificator__icontains=search_input)

        print_objects = print_objects.order_by('custom_order', '-id')

        paginator = Paginator(print_objects, settings.ROWS_PER_TABLE, 5)
        page = paginator.get_page(page_number)
        pagination = paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)

        if page.has_next():
            next_page = page.next_page_number()
        else:
            next_page = '…'

        if page.has_previous():
            previous_page = page.previous_page_number()
        else:
            previous_page = '…'

        for print_object in page:
            table.append(
                {
                    'id': print_object.id,
                    'row': [{'text': print_object.kiosk.name if print_object.kiosk else '-'},
                            {'text': print_object.identificator},
                            {'text': print_object.date.strftime(settings.TABLE_DATE_FORMAT)},
                            {'text': functions.calculate_print_cost(print_object.print_settings, print_object.kiosk.id if print_object.kiosk else None) if print_object.transaction is None else print_object.transaction.amount, 'currency': settings.CURRENCY_ICON_PATH},
                            {'text': _(print_object.status), 'status': print_object.status}]
                })

        return HttpResponse(render_to_string(template_name='dashboard/print_queue/print_queue_table.html', context={'table': table, 'pagination': pagination, 'next_page': next_page, 'previous_page': previous_page, 'current_page': page.number}))


def print_queue_action(request):
    if request.user.is_staff and request.method == 'POST':
        print_id = request.POST.get('print_id')
        action = request.POST.get('action')

        if action == 'view':
            print_object = models.Print.objects.get(id=print_id)
            print_settings = json.loads(print_object.print_settings)
            context = {
                'id': print_object.id,
                'title': _('Confirm to print') if print_object.status == 'await' else _('Print info'),
                'identificator': print_object.identificator,
                'print_settings': f'{_("Print settings")} : {print_settings["print_settings"]}<br> \
                    {_("Pages")} : {print_settings["pages"]}<br> \
                    {_("Copies")} : {print_settings["copies"]}<br> \
                        {_("Total pages")} : {print_settings["total_pages"]}',
                'replenishment': functions.calculate_print_cost(print_object.print_settings, print_object.kiosk.id if print_object.kiosk else None) - print_object.user.balance,
                'balance': print_object.user.balance,
                'amount': functions.calculate_print_cost(print_object.print_settings, print_object.kiosk.id if print_object.kiosk else None) if print_object.transaction is None else print_object.transaction.amount,
                'actions_allowed': True if print_object.status == 'await' else False,
                'replenishment_allowed': True if print_object.user.phone_number != settings.GUEST['phone_number'] else False
            }
            return HttpResponse(render_to_string(template_name='dashboard/print_queue/print_queue_view.html', context=context))

        elif action == 'print':
            print_object = models.Print.objects.get(id=print_id)
            print_object.status = 'printed'

            amount = abs(float(request.POST.get('amount', '0.0').replace(',', '.')))

            if print_object.user.phone_number != settings.GUEST['phone_number']:
                replenishment = abs(float(request.POST.get('replenishment', '0.0').replace(',', '.')))
                transaction = models.Transaction.objects.create(
                    identificator=print_object.identificator,
                    amount=amount,
                    type='withdrawal',
                    user=print_object.user,
                    confirming_user=request.user
                )
                transaction.save()

                print_object.transaction = transaction
                print_object.save()

                models.Transaction.objects.create(
                    identificator=print_object.identificator,
                    amount=replenishment,
                    type='replenishment',
                    user=print_object.user,
                    confirming_user=request.user
                ).save()

                user = models.User.objects.get(id=print_object.user.id)
                user.balance += (replenishment - amount)
                user.save()
            else:
                guest_user = models.User.objects.get(phone_number=settings.GUEST['phone_number'])
                transaction = models.Transaction.objects.create(
                    identificator=print_object.identificator,
                    amount=amount,
                    type='guest print',
                    user=guest_user,
                    confirming_user=request.user
                )
                transaction.save()
                print_object.transaction = transaction
                print_object.save()

            return HttpResponse('printed')

        elif action == 'cancel':
            print_object = models.Print.objects.get(id=print_id)
            print_object.status = 'canceled'
            print_object.save()

            return HttpResponse('canceled')


def users(request):
    if request.user.is_staff:
        context = {'dashboard_page': 'users', 'username': request.user.name}
        return render(request, template_name='dashboard/users/users.html', context=context)

    return redirect('login')


def users_table(request):
    if request.user.is_staff and request.method == 'POST':
        table = [

            {'row': [{'text': _('Email')},
                     {'text': _('Phone number')},
                     {'text': _('Balance')},
                     {'text': _('Action')}]},
        ]
        search_input = request.POST.get('search-input')
        page_number = int(request.POST.get('page_number', 1))

        if not request.user.is_superuser:
            user_objects = models.User.objects.exclude(is_staff=True).exclude(phone_number=settings.GUEST['phone_number'])
        else:
            user_objects = models.User.objects.exclude(phone_number=settings.GUEST['phone_number'])

        if search_input != '':
            user_objects = user_objects.filter(
                Q(phone_number__icontains=search_input)
                | Q(email__icontains=search_input)
                | Q(name__icontains=search_input)
            )

        if not request.user.is_superuser:
            user_objects = user_objects.union(models.User.objects.filter(id=request.user.id))

        user_objects = user_objects.order_by('id')

        paginator = Paginator(user_objects, settings.ROWS_PER_TABLE, 5)
        page = paginator.get_page(page_number)
        pagination = paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)

        if page.has_next():
            next_page = page.next_page_number()
        else:
            next_page = '…'

        if page.has_previous():
            previous_page = page.previous_page_number()
        else:
            previous_page = '…'

        for user_object in page:
            table.append(
                {
                    'id': user_object.id,
                    'row': [{'text': user_object.email if user_object.email is not None else '-'},
                            {'text': user_object.phone_number},
                            {'text': user_object.balance, 'currency': settings.CURRENCY_ICON_PATH},
                            {'actions': [(_('Transactions'), 'transactions'),
                                         (_('Replenish'), 'replenish'),
                                         (_('Edit'), 'view')]}]
                })
        return HttpResponse(render_to_string(template_name='dashboard/users/users_table.html', context={'table': table, 'pagination': pagination, 'next_page': next_page, 'previous_page': previous_page, 'current_page': page.number}))


def users_action(request):
    if request.user.is_staff and request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = None

        if user_id != 'null':
            user = models.User.objects.get(id=user_id)

        if action == 'transactions':
            table = [
                {'row': [{'text': _('Date')}, {'text': _('Amount')}, {'text': _('Type')}]},
            ]

            transaction_objects = models.Transaction.objects.filter(user=user)

            for transaction_object in transaction_objects:
                table.append(
                    {
                        'id': transaction_object.id,
                        'row': [{'text': transaction_object.date.strftime(settings.TABLE_DATE_FORMAT)},
                                {'text': transaction_object.amount, 'currency': settings.CURRENCY_ICON_PATH},
                                {'text': _(transaction_object.type), 'type': transaction_object.type}]
                    })

            return HttpResponse(render_to_string(template_name='dashboard/users/users_transactions.html', context={'table': table, 'title': user.phone_number}))

        elif action == 'replenish':
            return HttpResponse(render_to_string(template_name='dashboard/users/users_replenish.html', context={'id': user.id, 'title': user.phone_number, 'amounts': (10, 20, 30, 40, 50)}))

        elif action == 'view':
            context = {
                'id': user_id,
                'allow_stuff': True if request.user.is_superuser else False
            }

            if user_id != 'null':
                context['title'] = _('Edit user')
                context['form'] = forms.DashboardUserForm(models.User.objects.get(id=user_id))
            else:
                context['title'] = _('Create new user')
                context['form'] = forms.DashboardUserForm()

            return HttpResponse(render_to_string(template_name='dashboard/users/users_view.html', context=context))

        elif action == 'replenish_save':
            amount = float(request.POST.get('amount', '0.0').replace(',', '.'))
            models.Transaction.objects.create(
                identificator=user.phone_number,
                amount=abs(amount),
                type='replenishment' if amount >= 0 else 'withdrawal',
                user=user,
                confirming_user=request.user
            ).save()
            user.balance += amount
            user.save()

            return HttpResponse('replenish saved')

        elif action == 'view_save':
            form = forms.DashboardUserForm(user, request.POST)

            if form.is_valid():
                form.save()
                return HttpResponse('user saved')

            context = {
                'id': user_id,
                'form': form,
                'title': _('Edit user') if user_id != 'null' else _('Create new user'),
                'allow_stuff': True if request.user.is_superuser else False
            }

            return HttpResponse(render_to_string(template_name='dashboard/users/users_view.html', context=context))


def cashbox(request):
    if request.user.is_staff:
        context = {'dashboard_page': 'cashbox', 'username': request.user.name}
        return render(request, template_name='dashboard/cashbox/cashbox.html', context=context)

    return redirect('login')


def cashbox_table(request):
    if request.user.is_staff and request.method == 'POST':
        table = [

            {'row': [{'text': _('Date')},
                     {'text': _('Identificator')},
                     {'text': _('Employee')},
                     {'text': _('Amount')},
                     {'text': _('Type')}]},
        ]
        search_input = request.POST.get('search-input')
        page_number = int(request.POST.get('page_number', 1))
        date_from = request.POST.get('date-from')
        date_to = request.POST.get('date-to')

        transaction_objects = models.Transaction.objects.all()

        if date_from != '':
            transaction_objects = transaction_objects.filter(date__gte=datetime.strptime(date_from + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))

        if date_to != '':
            transaction_objects = transaction_objects.filter(date__lte=datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))

        if search_input != '':
            transaction_objects = transaction_objects.filter(
                Q(identificator__icontains=search_input)
                | Q(type__icontains=search_input)
                | Q(confirming_user__name__icontains=search_input)
            )

        transaction_objects = transaction_objects.order_by('-id')

        paginator = Paginator(transaction_objects, settings.ROWS_PER_TABLE)
        page = paginator.get_page(page_number)
        pagination = paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)

        if page.has_next():
            next_page = page.next_page_number()
        else:
            next_page = '…'

        if page.has_previous():
            previous_page = page.previous_page_number()
        else:
            previous_page = '…'

        for transaction_object in page:
            table.append(
                {
                    'id': transaction_object.id,
                    'row': [{'text': transaction_object.date.strftime(settings.TABLE_DATE_FORMAT)},
                            {'text': transaction_object.identificator},
                            {'text': transaction_object.confirming_user.name if transaction_object else '-'},
                            {'text': transaction_object.amount, 'currency': settings.CURRENCY_ICON_PATH},
                            {'text': _(transaction_object.type), 'type': transaction_object.type}]
                })

        return HttpResponse(render_to_string(template_name='dashboard/cashbox/cashbox_table.html', context={'table': table, 'pagination': pagination, 'next_page': next_page, 'previous_page': previous_page, 'current_page': page.number}))


def cashbox_action(request):
    if request.user.is_staff and request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        action = request.POST.get('action')

        if action == 'view':
            context = {
                'id': transaction_id,
                'types': ({'text': _('replenishment'), 'value': 'replenishment'},
                          {'text': _('withdrawal'), 'value': 'withdrawal'},
                          {'text': _('guest print'), 'value': 'guest print'}),
                'date': datetime.now().strftime('%Y-%m-%dT%H:%M'),
                'users': '___'.join([f'{user.phone_number} _ {user.name}' for user in models.User.objects.exclude(is_staff=True).exclude(phone_number=settings.GUEST['phone_number'])] + [f'{user.name}' for user in models.User.objects.filter(phone_number=settings.GUEST['phone_number'])])
            }
            return HttpResponse(render_to_string(template_name='dashboard/cashbox/cashbox_view.html', context=context))
        elif action == 'view_save':
            found_user = False
            user = request.POST.get('user')
            transaction_type = request.POST.get('type')
            amount = abs(float(request.POST.get('amount', '0.0').replace(',', '.')))
            if user == models.User.objects.get(phone_number=settings.GUEST['phone_number']).name:
                user = models.User.objects.get(phone_number=settings.GUEST['phone_number'])
                transaction_type = 'guest print'
                indicator = functions.get_next_guest_identificator()
                found_user = True
            else:
                if models.User.objects.filter(phone_number=user.split(' _ ')[0]).exists():
                    user = models.User.objects.get(phone_number=user.split(' _ ')[0])
                    indicator = user.phone_number

                    if transaction_type == 'replenishment':
                        user.balance += amount
                    elif transaction_type == 'withdrawal':
                        user.balance -= amount
                    user.save()

                    found_user = True
            if transaction_id == 'null' and found_user:
                models.Transaction.objects.create(
                    identificator=indicator,
                    amount=amount,
                    type=transaction_type,
                    user=user,
                    confirming_user=request.user
                ).save()

            return HttpResponse('transaction saved')


def prices(request):
    if request.user.is_staff:
        context = {'dashboard_page': 'prices', 'username': request.user.name}
        return render(request, template_name='dashboard/prices/prices.html', context=context)

    return redirect('login')


def prices_table(request):
    if request.user.is_staff and request.method == 'POST':
        table = [

            {'row': [{'text': _('Kiosk')},
                     {'text': _('Print parameters')},
                     {'text': _('Page range')},
                     {'text': _('Price')},
                     {'text': _('Edit')}]},
        ]
        search_input = request.POST.get('search-input')
        page_number = int(request.POST.get('page_number', 1))

        price_objects = models.Price.objects.all()

        if search_input != '':
            price_objects = price_objects.filter(
                Q(kiosk__name__icontains=search_input)
                | Q(print_settings__icontains=search_input)
            )

        price_objects = price_objects.order_by('print_settings', 'start_page')

        paginator = Paginator(price_objects, settings.ROWS_PER_TABLE)
        page = paginator.get_page(page_number)
        pagination = paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)

        if page.has_next():
            next_page = page.next_page_number()
        else:
            next_page = '…'

        if page.has_previous():
            previous_page = page.previous_page_number()
        else:
            previous_page = '…'

        for price_object in page:
            table.append(
                {
                    'id': price_object.id,
                    'row': [{'text': price_object.kiosk.name},
                            {'text': price_object.print_settings},
                            {'text': f'{price_object.start_page}-{price_object.end_page if price_object.end_page is not None else "…"}'},
                            {'text': price_object.price, 'currency': settings.CURRENCY_ICON_PATH},
                            {'text': ''}]
                })

        return HttpResponse(render_to_string(template_name='dashboard/prices/prices_table.html', context={'table': table, 'pagination': pagination, 'next_page': next_page, 'previous_page': previous_page, 'current_page': page.number}))


def prices_action(request):
    if request.user.is_staff and request.method == 'POST':
        price_id = request.POST.get('price_id')
        action = request.POST.get('action')

        if action == 'view':
            price_object = models.Price.objects.get(id=price_id)
            context = {
                'kiosk': price_object.kiosk.name,
                'print_settings': price_object.print_settings,
                'start_page': price_object.start_page,
                'end_page': price_object.end_page if price_object.end_page is not None else '',
                'price': price_object.price,
                'can_delete': False if price_object.base_price is None else True,
                'id': price_id
            }
            return HttpResponse(render_to_string(template_name='dashboard/prices/prices_view.html', context=context))
        elif action == 'view_save':
            price_object = models.Price.objects.get(id=price_id)

            if request.POST.get('start_page', '') != '':
                start_page = abs(int(request.POST.get('start_page').replace(',', '.').split('.')[0]))
            else:
                start_page = 1
            if request.POST.get('end_page', '') != '':
                end_page = abs(int(request.POST.get('end_page').replace(',', '.').split('.')[0]))
            else:
                end_page = None

            price = abs(float(request.POST.get('price', '0.0').replace(',', '.')))

            models.Price.change_range(price_object.id, start_page, end_page, price)

            return HttpResponse('price saved')

        elif action == 'view_delete':
            price_object = models.Price.objects.get(id=price_id)
            models.Price.delete_range(price_object.id)
            return HttpResponse('price deleted')


def kiosks(request):
    if request.user.is_staff:
        context = {'dashboard_page': 'kiosks', 'username': request.user.name}
        return render(request, template_name='dashboard/kiosks/kiosks.html', context=context)

    return redirect('login')


def kiosks_table(request):
    if request.user.is_staff and request.method == 'POST':
        table = [

            {'row': [{'text': _('Kiosk')},
                     {'text': _('Key')},
                     {'text': _('Status')},
                     {'text': _('Actions')}]},
        ]
        search_input = request.POST.get('search-input')

        kiosk_objects = models.Kiosk.objects.all()

        if search_input != '':
            kiosk_objects = kiosk_objects.filter(
                Q(name__icontains=search_input)
                | Q(status__icontains=search_input)
            )

        kiosk_objects = kiosk_objects.order_by('id')

        for kiosk_objects in kiosk_objects:
            table.append(
                {
                    'id': kiosk_objects.id,
                    'row': [{'text': kiosk_objects.name},
                            {'text': kiosk_objects.key},
                            {'text': _(kiosk_objects.status), 'status': kiosk_objects.status},
                            {'action': 'stop' if kiosk_objects.status == 'active' else ('disabled' if kiosk_objects.status == 'disabled' else 'start')}]
                })

        return HttpResponse(render_to_string(template_name='dashboard/kiosks/kiosks_table.html', context={'table': table}))


def kiosks_action(request):
    if request.user.is_staff and request.method == 'POST':
        kiosk_id = request.POST.get('kiosk_id')
        action = request.POST.get('action')

        if action == 'view':
            context = {
                'key': uuid.uuid4().__str__(),
                'id': kiosk_id
            }
            return HttpResponse(render_to_string(template_name='dashboard/kiosks/kiosks_view.html', context=context))

        elif action == 'start':
            kiosk_object = models.Kiosk.objects.get(id=kiosk_id)
            kiosk_object.status = 'active'
            kiosk_object.save()

            return HttpResponse('started')

        elif action == 'stop':
            kiosk_object = models.Kiosk.objects.get(id=kiosk_id)
            kiosk_object.status = 'error'
            kiosk_object.save()

            return HttpResponse('stoped')

        elif action == 'delete':
            models.Kiosk.objects.get(id=kiosk_id).delete()
            return HttpResponse('deleted')

        elif action == 'view_save':
            name = request.POST.get('name')
            key = request.POST.get('key')
            models.Kiosk.objects.create(
                name=name,
                key=key
            ).save()
            return HttpResponse('kiosk saved')


def statistics(request):
    if request.user.is_superuser:
        context = {'dashboard_page': 'statistics', 'username': request.user.name, 'date_from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}
        return render(request, template_name='dashboard/statistics/statistics.html', context=context)

    return redirect('login')


def statistics_page(request):
    def none_to_zero(value):
        if value is None:
            return 0
        return value

    def get_pupular_print_settings(print_objects):
        price_objects = models.Price.objects.filter(base_price=None)

        prices = {}
        for price in price_objects:
            prices[price.kiosk.name + ' _ ' + price.print_settings] = str(print_objects.filter(kiosk=price.kiosk, print_settings__icontains=price.print_settings).count())

        return dict(sorted(prices.items(), key=lambda item: item[1], reverse=True)[:10])

    if request.user.is_superuser:
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        print_objects = models.Print.objects.exclude(status='canceled').order_by('id')
        transaction_objects = models.Transaction.objects.all().order_by('id')
        if date_from != '':
            date_from = datetime.strptime(date_from + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
            print_objects = print_objects.filter(date__gte=date_from)
            transaction_objects = transaction_objects.filter(date__gte=date_from)
        else:
            date_1 = print_objects.first()
            date_2 = transaction_objects.first()
            if date_1 is not None and date_2 is not None:
                date_from = date_1.date if date_1.date < date_2.date else date_2.date
            else:
                date_from = (datetime.now() - timedelta(days=30))

        if date_to != '':
            date_to = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            print_objects = print_objects.filter(date__lte=date_to)
            transaction_objects = transaction_objects.filter(date__lte=date_to)
        else:
            date_1 = print_objects.last()
            date_2 = transaction_objects.last()
            if date_1 is not None and date_2 is not None:
                date_to = date_1.date if date_1.date < date_2.date else date_2.date
            else:
                date_to = datetime.now()

        dates = [date_from.date() + timedelta(days=x) for x in range((date_to.date() - date_from.date()).days + 1)]

        guests_print_objects = print_objects.filter(user__phone_number=settings.GUEST['phone_number'])
        users_print_objects = print_objects.exclude(user__phone_number=settings.GUEST['phone_number'])

        guests_transaction_objects = transaction_objects.filter(type='guest print')
        users_transaction_objects = transaction_objects.filter(type='withdrawal')

        popular_print_settings = get_pupular_print_settings(print_objects)

        context = {
            'printouts': {
                'total': print_objects.count(),
                'registered_users': users_print_objects.count(),
                'guests': guests_print_objects.count(),
            },
            'incomes': {
                'total': none_to_zero(transaction_objects.exclude(type='withdrawal').aggregate(Sum('amount'))['amount__sum']),
                'registered_users': none_to_zero(transaction_objects.filter(type='withdrawal').aggregate(Sum('amount'))['amount__sum']),
                'guests': none_to_zero(transaction_objects.filter(type='guest print').aggregate(Sum('amount'))['amount__sum']),
                'balances': none_to_zero(transaction_objects.filter(type='replenishment').aggregate(Sum('amount'))['amount__sum']) - none_to_zero(transaction_objects.filter(type='withdrawal').aggregate(Sum('amount'))['amount__sum']),
            },
            'print_per_days': {
                'labels': '~~~'.join([date.strftime('%d.%m.%y') for date in dates]),
                'registered_users_data': '~~~'.join([str(users_print_objects.filter(date__date=date).count()) for date in dates]),
                'guests_data': '~~~'.join([str(guests_print_objects.filter(date__date=date).count()) for date in dates])
            },
            'income_per_days': {
                'labels': '~~~'.join([date.strftime('%d.%m.%y') for date in dates]),
                'registered_users_data': '~~~'.join([str(none_to_zero(users_transaction_objects.filter(date__date=date).aggregate(Sum('amount'))['amount__sum'])) for date in dates]),
                'guests_data': '~~~'.join([str(none_to_zero(guests_transaction_objects.filter(date__date=date).aggregate(Sum('amount'))['amount__sum'])) for date in dates])
            },
            'popular_print_settings': {
                'labels': '~~~'.join(popular_print_settings.keys()),
                'data': '~~~'.join(popular_print_settings.values())
            }
        }
        return HttpResponse(render_to_string(template_name='dashboard/statistics/statistics_page.html', context=context))

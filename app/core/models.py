"""
Standart models.
"""
from django.db import models, transaction
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
import uuid


class UserManager(BaseUserManager):
    """Manager for users."""
    def create_user(self, phone_number, password=None, **kw):
        """Create, save and return new user."""
        if not phone_number or phone_number == '':
            raise ValueError("User must have phone number.")
        user = self.model(phone_number=self.normalize_phone_number(phone_number), **kw)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_superuser(self, phone_number, password=None, **kw):
        """Create and return new Superuser."""
        return self.create_user(phone_number,
                                password,
                                is_staff=True,
                                is_superuser=True,
                                **kw
                                )

    def normalize_phone_number(self, phone_number):
        return phone_number.replace(' ', '').replace('+', '').replace('-', '')


class User(AbstractBaseUser, PermissionsMixin):
    """User model."""
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, default='', blank=True)

    note = models.TextField(blank=True)

    balance = models.FloatField(default=0.0)
    allow_credit = models.BooleanField(default=False)

    discount = models.ManyToManyField('Discount', blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_number'

    objects = UserManager()


class Discount(models.Model):
    name = models.CharField(max_length=50)
    percent = models.FloatField(default=0.0)
    expire = models.DateTimeField(null=True, blank=True)
    permanent_discount = models.BooleanField()

    def __str__(self):
        return f'{self.name} ___ {self.percent}%'


class Print(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    print_settings = models.TextField()
    identificator = models.CharField(max_length=50, default='', blank=True)
    status_choices = [
        ('await', 'await'),
        ('printed', 'printed'),
        ('canceled', 'canceled')
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='await')

    kiosk = models.ForeignKey('Kiosk', null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    transaction = models.ForeignKey('Transaction', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'{self.date.strftime("%Y.%m.%d %H:%M:%S")} --- {self.identificator} --- {self.user}'


class Transaction(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    identificator = models.CharField(max_length=50, default='', blank=True)
    amount = models.FloatField(default=0.0)
    type_choices = [
        ('replenishment', 'replenishment'),
        ('withdrawal', 'withdrawal'),
        ('guest print', 'guest print')
    ]
    type = models.CharField(max_length=15, choices=type_choices, default='guest print')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='user')
    confirming_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='confirming_user')

    def __str__(self):
        return f'{self.date.strftime("%Y.%m.%d %H:%M:%S")} --- {self.identificator} --- {self.amount}'


class Kiosk(models.Model):
    name = models.CharField(max_length=50, default='Kiosk')
    key = models.UUIDField(default=uuid.uuid4)
    configured_printers = models.TextField()
    status_choices = [
        ('error', 'error'),
        ('active', 'active'),
        ('disabled', 'disabled')
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='disabled')

    def __str__(self):
        return self.name


class Price(models.Model):
    print_settings = models.TextField()
    start_page = models.IntegerField(default=1)
    end_page = models.IntegerField(null=True, blank=True)
    price = models.FloatField(default=0.0)

    kiosk = models.ForeignKey('Kiosk', on_delete=models.CASCADE)
    base_price = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='same_price')

    def __str__(self):
        return f'{self.kiosk} --- {self.print_settings} --- {self.start_page}:{self.end_page}'

    @classmethod
    @transaction.atomic
    def change_range(cls, price_id: int, start_page: int, end_page: int, price: float):
        price_object = cls.objects.get(id=price_id)

        base_price = price_object if price_object.base_price is None else price_object.base_price
        same_price_objects = base_price.same_price.all()

        if start_page < price_object.start_page:
            previous_price_range = same_price_objects.filter(start_page__gte=start_page, end_page__lte=start_page).first()
            if previous_price_range.start_page != previous_price_range.end_page or previous_price_range.start_page > start_page:
                previous_price_range.end_page = start_page - 1
            else:
                previous_price_range.delete()

            middle_price_range = same_price_objects.filter(start_page__gt=previous_price_range.end_page).order_by('start_page')
            for price_pange in middle_price_range:
                if price_pange.id != price_object.id:
                    price_pange.delete()
                else:
                    break

            price_object.start_page = start_page
            price_object.price = price

        elif start_page > price_object.start_page and start_page <= price_object.end_page:
            previous_price_range = same_price_objects.filter(end_page=price_object.start_page - 1).first()
            if previous_price_range is not None:
                previous_price_range.end_page = start_page - 1
                previous_price_range.save()
            else:
                cls.objects.create(
                    print_settings=base_price.print_settings,
                    start_page=price_object.start_page,
                    end_page=start_page - 1,
                    price=price_object.price,
                    base_price=base_price,
                    kiosk=base_price.kiosk
                )

            price_object.start_page = start_page
            price_object.price = price

        elif end_page is not None and price_object.end_page is None:
            cls.objects.create(
                print_settings=base_price.print_settings,
                start_page=price_object.start_page,
                end_page=end_page,
                price=price,
                base_price=base_price,
                kiosk=base_price.kiosk
            ).save()

            price_object.start_page = end_page + 1

        elif end_page is not None and end_page > price_object.end_page:
            next_price_range = same_price_objects.filter(start_page__gte=end_page, end_page__lte=end_page).first()
            if next_price_range is not None:
                if next_price_range.start_page != next_price_range.end_page or next_price_range.end_page < end_page:
                    next_price_range.start_page = end_page + 1
                else:
                    next_price_range.delete()

                middle_price_range = same_price_objects.filter(end_page__lt=next_price_range.start_page).order_by('-start_page')
                for price_pange in middle_price_range:
                    if price_pange.id != price_object.id:
                        price_pange.delete()
                    else:
                        break

            else:
                price_object.end_page = end_page
                price_object.price = price

                base_price.start_page = end_page + 1
                base_price.save()

        elif end_page is not None and end_page < price_object.end_page and end_page >= price_object.start_page:
            next_price_range = same_price_objects.filter(start_page=price_object.end_page + 1).first()
            next_price_range.start_page = end_page - 1
            next_price_range.save()

            price_object.end_page = start_page
            price_object.price = price

        elif end_page is None and price_object.end_page is not None:
            base_price.start_page = price_object.start_page
            base_price.price = price
            price_object.delete()

        elif start_page == price_object.start_page and end_page == price_object.end_page:
            price_object.price = price

        price_object.save()

    @classmethod
    @transaction.atomic
    def delete_range(cls, price_id):
        price_object = cls.objects.get(id=price_id)

        if price_object.base_price is not None:
            same_price_objects = price_object.base_price.same_price.all()
            next_price_range = same_price_objects.filter(start_page=price_object.end_page + 1).first()

            if next_price_range is not None:
                next_price_range.start_page = price_object.start_page
                next_price_range.save()

            else:
                price_object.base_price.start_page = price_object.start_page
                price_object.base_price.save()

            price_object.delete()


class EmailMessage(models.Model):
    email = models.EmailField(max_length=50)
    message_id = models.CharField(max_length=255)
    file_names = models.TextField(blank=True)

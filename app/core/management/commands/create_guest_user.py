from django.core.management.base import BaseCommand
from core import models
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not models.User.objects.filter(phone_number=settings.GUEST['phone_number']).exists():
            guest_user = models.User.objects.create_user(phone_number=settings.GUEST['phone_number'], name='Guest', email='')
            guest_user.set_password(settings.GUEST['password'])
            guest_user.save()
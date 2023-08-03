"""
Django command to wait for the Database to be available.
"""

from django.core.management.base import BaseCommand
from time import sleep

from psycopg2 import OperationalError as Psycopg2Error
from django.db.utils import OperationalError


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Run wait for Database..."))
        db_is_up = False
        while db_is_up is False:
            try:
                self.check(databases=['default'])
                db_is_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write(
                    self.style.NOTICE("Database unavailable..."))
                sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available.'))

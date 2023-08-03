#!/bin/sh
set -e

python manage.py wait_for_db
python manage.py tailwind install --no-input
python manage.py tailwind build --no-input
echo yes | python manage.py collectstatic
python manage.py migrate
python manage.py create_guest_user
python manage.py compilemessages

daphne --bind "0.0.0.0" app.asgi:application

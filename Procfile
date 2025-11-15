web: daphne promptcraft.asgi:application --port $PORT --bind 0.0.0.0 -v2
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput

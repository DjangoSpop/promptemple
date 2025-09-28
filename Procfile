web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && daphne promptcraft.asgi:application --bind 0.0.0.0 --port $PORT
worker: celery -A promptcraft worker --loglevel=info
beat: celery -A promptcraft beat --loglevel=info
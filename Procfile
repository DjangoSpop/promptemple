# Heroku Procfile - Optimized for MVP (No Celery, No Daphne)
# Using Gunicorn for better performance and stability

# Web dyno: Run migrations, collect static files, start Gunicorn
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn promptcraft.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-file -

# Optional: Release phase (runs before web dyno starts)
# Uncomment if you want migrations to run automatically on each deploy
# release: python manage.py migrate --noinput
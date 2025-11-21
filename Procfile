# Heroku Procfile - Optimized for MVP (No Celery, No Daphne)
# Using Gunicorn for better performance and stability

# Web dyno: Skip migrations (database already initialized), skip collectstatic (using WhiteNoise), start Gunicorn
web: gunicorn promptcraft.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-file -

# Optional: Release phase (runs before web dyno starts)
# Uncomment if you want migrations to run automatically on each deploy
# release: python manage.py migrate --noinput
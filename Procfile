# Heroku Procfile - Daphne ASGI server with WebSocket support

# Web dyno: Daphne serves HTTP + WebSocket via ASGI
web: daphne -b 0.0.0.0 -p $PORT promptcraft.asgi:application

# Optional: Release phase (runs before web dyno starts)
# release: python manage.py migrate --noinput

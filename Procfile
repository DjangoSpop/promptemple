# Heroku Procfile - Gunicorn WSGI (HTTP + SSE only, no WebSocket)
# Reverted from Daphne: async thread pool was exhausting Postgres connections

web: gunicorn promptcraft.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-file -

# Production deployment configuration for Daphne ASGI server

# Basic Daphne command for development
daphne-dev:
	daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application

# Production Daphne with optimizations
daphne-prod:
	daphne \
		--bind 0.0.0.0 \
		--port 8000 \
		--proxy-headers \
		--access-log logs/daphne_access.log \
		--application-close-timeout 30 \
		--websocket-timeout 86400 \
		--websocket-connect-timeout 10 \
		--verbosity 2 \
		promptcraft.asgi:application

# Daphne with SSL/TLS (requires SSL_CERT_PATH and SSL_KEY_PATH environment variables)
daphne-ssl:
	daphne \
		--bind 0.0.0.0 \
		--port 443 \
		--tls-cert $(SSL_CERT_PATH) \
		--tls-key $(SSL_KEY_PATH) \
		--proxy-headers \
		--access-log logs/daphne_access.log \
		--application-close-timeout 30 \
		--websocket-timeout 86400 \
		--websocket-connect-timeout 10 \
		promptcraft.asgi:application

# Install dependencies
install-deps:
	pip install -r requirements.txt

# Create log directories
setup-logs:
	mkdir -p logs

# Initialize Redis (for development)
redis-start:
	redis-server --daemonize yes --port 6379

# Stop Redis
redis-stop:
	redis-cli shutdown

# Run full stack (Redis + Daphne)
start-stack: setup-logs redis-start daphne-prod

# Health check
health-check:
	curl -f http://localhost:8000/health/ || exit 1

# WebSocket test
ws-test:
	@echo "Testing WebSocket connection..."
	@python -c "import asyncio, websockets; \
	async def test(): \
		async with websockets.connect('ws://localhost:8000/ws/chat/test/') as ws: \
			await ws.send('{\"type\": \"ping\"}'); \
			response = await ws.recv(); \
			print(f'WebSocket test successful: {response}'); \
	asyncio.run(test())"

.PHONY: daphne-dev daphne-prod daphne-ssl install-deps setup-logs redis-start redis-stop start-stack health-check ws-test
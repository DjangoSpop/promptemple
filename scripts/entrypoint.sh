#!/bin/bash
# Production-ready entrypoint script for Docker deployment
# Handles database migrations, static files, and graceful shutdown

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
}

# Wait for database to be ready
wait_for_db() {
    log "Waiting for database connection..."
    
    # Extract database info from DATABASE_URL if available
    if [ -n "$DATABASE_URL" ]; then
        # Parse DATABASE_URL to get host and port
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    fi
    
    # Use environment variables or defaults
    DB_HOST=${DB_HOST:-${DB_HOST:-localhost}}
    DB_PORT=${DB_PORT:-${DB_PORT:-5432}}
    
    # Wait for database connection
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
            log_success "Database is ready on $DB_HOST:$DB_PORT"
            return 0
        fi
        
        log "Database not ready. Attempt $attempt/$max_attempts. Waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Database connection failed after $max_attempts attempts"
    exit 1
}

# Wait for Redis to be ready (if configured)
wait_for_redis() {
    if [ -n "$REDIS_URL" ]; then
        log "Waiting for Redis connection..."
        
        # Extract Redis info
        REDIS_HOST=$(echo $REDIS_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        if [ -z "$REDIS_HOST" ]; then
            REDIS_HOST=$(echo $REDIS_URL | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
        fi
        REDIS_PORT=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        REDIS_HOST=${REDIS_HOST:-localhost}
        REDIS_PORT=${REDIS_PORT:-6379}
        
        max_attempts=15
        attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if nc -z "$REDIS_HOST" "$REDIS_PORT" 2>/dev/null; then
                log_success "Redis is ready on $REDIS_HOST:$REDIS_PORT"
                return 0
            fi
            
            log "Redis not ready. Attempt $attempt/$max_attempts. Waiting..."
            sleep 1
            attempt=$((attempt + 1))
        done
        
        log_warning "Redis connection failed, continuing without Redis"
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    if ! python manage.py migrate --noinput; then
        log_error "Database migrations failed"
        exit 1
    fi
    
    log_success "Database migrations completed"
}

# Collect static files
collect_static() {
    log "Collecting static files..."
    
    if ! python manage.py collectstatic --noinput --clear; then
        log_error "Static file collection failed"
        exit 1
    fi
    
    log_success "Static files collected"
}

# Create superuser if specified
create_superuser() {
    if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log "Creating superuser..."
        
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
        username='admin'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF
        
        log_success "Superuser setup completed"
    fi
}

# Validate configuration
validate_config() {
    log "Validating Django configuration..."
    
    if ! python manage.py check --deploy; then
        log_error "Django configuration validation failed"
        exit 1
    fi
    
    log_success "Configuration validation passed"
}

# Health check function
health_check() {
    log "Performing initial health check..."
    
    # Check if we can import Django settings
    if ! python -c "import django; django.setup()"; then
        log_error "Django setup failed"
        return 1
    fi
    
    # Check database connection
    if ! python manage.py shell -c "from django.db import connection; connection.ensure_connection()"; then
        log_error "Database health check failed"
        return 1
    fi
    
    log_success "Health check passed"
    return 0
}

# Signal handlers for graceful shutdown
cleanup() {
    log "Received shutdown signal, cleaning up..."
    
    # Kill background processes
    jobs -p | xargs -r kill
    
    log_success "Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    log "Starting PromptCraft application deployment..."
    log "Environment: ${DJANGO_ENVIRONMENT:-development}"
    log "Settings module: ${DJANGO_SETTINGS_MODULE:-promptcraft.settings}"
    
    # Pre-deployment checks
    if [ "$SKIP_CHECKS" != "true" ]; then
        wait_for_db
        wait_for_redis
        validate_config
    else
        log_warning "Skipping pre-deployment checks (SKIP_CHECKS=true)"
    fi
    
    # Database setup
    if [ "$SKIP_MIGRATIONS" != "true" ]; then
        run_migrations
    else
        log_warning "Skipping migrations (SKIP_MIGRATIONS=true)"
    fi
    
    # Static files
    if [ "$SKIP_STATIC" != "true" ]; then
        collect_static
    else
        log_warning "Skipping static file collection (SKIP_STATIC=true)"
    fi
    
    # Superuser creation
    if [ "$CREATE_SUPERUSER" = "true" ]; then
        create_superuser
    fi
    
    # Final health check
    if ! health_check; then
        log_error "Final health check failed"
        exit 1
    fi
    
    log_success "Pre-deployment setup completed successfully"
    log "Starting application server..."
    
    # Execute the main command
    exec "$@"
}

# Run main function with all arguments
main "$@"
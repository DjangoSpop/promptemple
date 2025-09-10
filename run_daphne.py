#!/usr/bin/env python
"""
Production ASGI server configuration using Daphne
Optimized for WebSocket performance and scalability
"""

import os
import sys
import logging
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'logs' / 'daphne.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the Daphne ASGI server"""
    try:
        from daphne.cli import CommandLineInterface
        from django.core.management import execute_from_command_line
        
        # Ensure Django is set up
        import django
        django.setup()
        
        logger.info("Starting Daphne ASGI server...")
        
        # Daphne command line arguments
        daphne_args = [
            'daphne',
            '--bind', '0.0.0.0',
            '--port', os.environ.get('PORT', '8000'),
            '--access-log', str(BASE_DIR / 'logs' / 'daphne_access.log'),
            '--application-close-timeout', '30',
            '--websocket-timeout', '86400',  # 24 hours for long connections
            '--websocket-connect-timeout', '10',
            '--proxy-headers',
            'promptcraft.asgi:application'
        ]
        
        # Add SSL configuration if certificates are available
        ssl_cert = os.environ.get('SSL_CERT_PATH')
        ssl_key = os.environ.get('SSL_KEY_PATH')
        
        if ssl_cert and ssl_key:
            daphne_args.extend(['--tls-cert', ssl_cert, '--tls-key', ssl_key])
            logger.info("SSL/TLS enabled for Daphne server")
        
        # Start Daphne
        sys.argv = daphne_args
        CommandLineInterface().run()
        
    except ImportError:
        logger.error("Daphne not installed. Install with: pip install daphne")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start Daphne server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
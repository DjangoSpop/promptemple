"""
Core WebSocket consumers for general app functionality
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class RootWebSocketConsumer(AsyncWebsocketConsumer):
    """
    Root WebSocket consumer that handles connections to ws://localhost:8000/
    This provides a general-purpose WebSocket endpoint for testing and basic functionality
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        self.room_name = "general"
        self.room_group_name = f"general_{self.room_name}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket connection established',
            'status': 'connected',
            'timestamp': self.get_timestamp()
        }))
        
        logger.info(f"WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected: {self.channel_name} (code: {close_code})")
    
    async def receive(self, text_data):
        """Handle received WebSocket message"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'unknown')
            message = text_data_json.get('message', '')
            
            logger.info(f"WebSocket message received: {message_type} - {message}")
            
            # Handle different message types
            if message_type == 'ping':
                await self.send_pong()
            elif message_type == 'echo':
                await self.send_echo(message)
            elif message_type == 'broadcast':
                await self.broadcast_message(message)
            else:
                await self.send_error('Unknown message type')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await self.send_error('Server error')
    
    async def send_pong(self):
        """Send pong response to ping"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'message': 'pong',
            'timestamp': self.get_timestamp()
        }))
    
    async def send_echo(self, message):
        """Echo message back to sender"""
        await self.send(text_data=json.dumps({
            'type': 'echo_response',
            'message': f'Echo: {message}',
            'timestamp': self.get_timestamp()
        }))
    
    async def broadcast_message(self, message):
        """Broadcast message to all connected clients in the room"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message_handler',
                'message': message,
                'sender': self.channel_name
            }
        )
    
    async def broadcast_message_handler(self, event):
        """Handle broadcast message from group"""
        message = event['message']
        sender = event['sender']
        
        # Don't send the message back to the sender
        if sender != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'broadcast',
                'message': message,
                'timestamp': self.get_timestamp()
            }))
    
    async def send_error(self, error_message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'timestamp': self.get_timestamp()
        }))
    
    def get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


class HealthCheckConsumer(AsyncWebsocketConsumer):
    """
    Simple health check WebSocket consumer
    """
    
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'health_check',
            'status': 'healthy',
            'message': 'WebSocket server is running',
            'timestamp': self.get_timestamp()
        }))
        await self.close()
    
    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()
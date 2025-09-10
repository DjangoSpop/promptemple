"""
Socket.IO compatible WebSocket consumer for Django Channels
"""
import json
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)

class SocketIOCompatibilityConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that mimics Socket.IO protocol for frontend compatibility
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.room_group_name = None
        self.user = None

    async def connect(self):
        """Handle WebSocket connection with Socket.IO-like protocol"""
        try:
            # Extract session info from query parameters
            query_string = self.scope.get("query_string", b"").decode()
            self.session_id = self.extract_session_id(query_string)
            
            if not self.session_id:
                self.session_id = str(uuid.uuid4())
            
            # Set up room group for this session
            self.room_group_name = f"socketio_{self.session_id}"
            
            # Get user from scope (if authenticated)
            self.user = self.scope.get("user", AnonymousUser())
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Accept connection
            await self.accept()
            
            # Send Socket.IO-like connection acknowledgment
            await self.send_socketio_message("0", {
                "sid": self.session_id,
                "upgrades": ["websocket"],
                "pingInterval": 25000,
                "pingTimeout": 20000
            })
            
            # Send connect message
            await self.send_socketio_message("40", {
                "type": "connect",
                "namespace": "/",
                "data": {"sid": self.session_id}
            })
            
            logger.info(f"Socket.IO compatible connection established: session={self.session_id}")
            
        except Exception as e:
            logger.error(f"Socket.IO connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"Socket.IO disconnected: session={self.session_id}, code={close_code}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages with Socket.IO protocol parsing"""
        try:
            # Parse Socket.IO message format
            message_type, data = self.parse_socketio_message(text_data)
            
            if message_type == "ping":
                # Respond to ping with pong
                await self.send_socketio_message("3", {})
                
            elif message_type == "message":
                # Handle chat message
                await self.handle_chat_message(data)
                
            elif message_type == "event":
                # Handle custom events
                await self.handle_custom_event(data)
                
            else:
                logger.warning(f"Unknown Socket.IO message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Socket.IO receive error: {e}")
            await self.send_error_message(str(e))

    def extract_session_id(self, query_string):
        """Extract session ID from query parameters"""
        try:
            # Parse EIO and transport parameters
            params = {}
            for param in query_string.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key] = value
            
            # Generate session ID based on connection
            return f"session_{uuid.uuid4().hex[:8]}"
            
        except Exception:
            return None

    def parse_socketio_message(self, text_data):
        """Parse Socket.IO message format"""
        try:
            if text_data.startswith("2"):
                # Ping message
                return "ping", {}
            elif text_data.startswith("42"):
                # Event message with JSON data
                json_data = text_data[2:]
                data = json.loads(json_data)
                return "event", data
            elif text_data.startswith("4"):
                # Message
                json_data = text_data[1:]
                data = json.loads(json_data) if json_data else {}
                return "message", data
            else:
                # Default to message
                try:
                    data = json.loads(text_data)
                    return "message", data
                except json.JSONDecodeError:
                    return "message", {"text": text_data}
                    
        except Exception as e:
            logger.error(f"Error parsing Socket.IO message: {e}")
            return "message", {"text": text_data}

    async def send_socketio_message(self, message_type, data):
        """Send message in Socket.IO format"""
        try:
            if message_type == "0":
                # Engine.IO handshake
                message = f"{message_type}{json.dumps(data)}"
            elif message_type == "40":
                # Socket.IO connect
                message = message_type
            elif message_type == "42":
                # Socket.IO event
                message = f"{message_type}{json.dumps(data)}"
            elif message_type == "3":
                # Pong
                message = message_type
            else:
                message = json.dumps(data)
                
            await self.send(text_data=message)
            
        except Exception as e:
            logger.error(f"Error sending Socket.IO message: {e}")

    async def handle_chat_message(self, data):
        """Handle chat messages"""
        try:
            message_text = data.get("message", "") if isinstance(data, dict) else str(data)
            
            # Broadcast to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message_text,
                    "user": str(self.user) if self.user else "Anonymous",
                    "session_id": self.session_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")

    async def handle_custom_event(self, data):
        """Handle custom events from frontend"""
        try:
            if isinstance(data, list) and len(data) > 0:
                event_name = data[0]
                event_data = data[1] if len(data) > 1 else {}
                
                # Handle different event types
                if event_name == "prompt_optimization":
                    await self.handle_prompt_optimization(event_data)
                elif event_name == "template_search":
                    await self.handle_template_search(event_data)
                else:
                    # Echo back unknown events
                    await self.send_socketio_message("42", ["response", {
                        "event": event_name,
                        "status": "received",
                        "data": event_data
                    }])
                    
        except Exception as e:
            logger.error(f"Error handling custom event: {e}")

    async def handle_prompt_optimization(self, data):
        """Handle prompt optimization requests"""
        try:
            prompt = data.get("prompt", "")
            # Simulate prompt optimization (replace with actual AI service)
            optimized_prompt = f"Optimized: {prompt}"
            
            await self.send_socketio_message("42", ["prompt_optimized", {
                "original": prompt,
                "optimized": optimized_prompt,
                "improvements": ["Clarity enhanced", "Context added"],
                "session_id": self.session_id
            }])
            
        except Exception as e:
            logger.error(f"Error in prompt optimization: {e}")

    async def handle_template_search(self, data):
        """Handle template search requests"""
        try:
            query = data.get("query", "")
            # Simulate template search (replace with actual search service)
            results = [
                {"id": 1, "title": f"Template for: {query}", "description": "Sample template"},
                {"id": 2, "title": f"Advanced {query} template", "description": "Advanced sample"}
            ]
            
            await self.send_socketio_message("42", ["search_results", {
                "query": query,
                "results": results,
                "total": len(results),
                "session_id": self.session_id
            }])
            
        except Exception as e:
            logger.error(f"Error in template search: {e}")

    async def send_error_message(self, error_msg):
        """Send error message to client"""
        await self.send_socketio_message("42", ["error", {
            "message": error_msg,
            "session_id": self.session_id
        }])

    # Group message handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send_socketio_message("42", ["chat_message", {
            "message": event["message"],
            "user": event["user"],
            "session_id": event["session_id"]
        }])
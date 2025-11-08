"""
Ask-Me API Views

Implements the 4 core endpoints for the Ask-Me prompt builder:
1. POST /askme/start - Start a new session
2. POST /askme/answer - Answer a question
3. POST /askme/finalize - Generate final prompt
4. GET /askme/stream - Stream updates (SSE)
"""

import json
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import AskMeSession, AskMeQuestion
from .askme_service import get_askme_service, PlannerResult, ComposerResult
from .serializers import AskMeSessionSerializer

logger = logging.getLogger(__name__)

class AskMeStartView(View):
    """Start a new Ask-Me session"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            logger.info(f"Received request: {request.method} {request.path}")
            logger.info(f"Request body: {request.body}")
            logger.info(f"Content type: {request.content_type}")

            # More robust JSON parsing with better error handling
            raw_body = request.body
            if isinstance(raw_body, bytes):
                raw_body = raw_body.decode('utf-8')
            
            logger.info(f"Decoded body string: {repr(raw_body)}")
            
            # Check for empty body
            if not raw_body.strip():
                return JsonResponse({
                    'error': 'Request body is empty'
                }, status=400)
            
            try:
                data = json.loads(raw_body)
                logger.info(f"Successfully parsed JSON data: {data}")
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON decode error: {json_error}")
                logger.error(f"Error at position {json_error.pos}: {repr(raw_body[max(0, json_error.pos-10):json_error.pos+10])}")
                return JsonResponse({
                    'error': 'Invalid JSON format',
                    'details': str(json_error)
                }, status=400)

            intent = data.get('intent', '')
            logger.info(f"Intent: {intent}")

            if not intent:
                return JsonResponse({
                    'error': 'Intent is required'
                }, status=400)

            logger.info("Creating new AskMe session...")

            # Create new session
            session = AskMeSession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                intent=intent
            )
            logger.info(f"Session created with ID: {session.id}")

            # Initialize the spec
            session.initialize_spec()
            logger.info(f"Session spec initialized: {session.spec}")

            # Get the AskMe service and plan initial questions
            logger.info("Getting AskMe service...")
            service = get_askme_service()
            logger.info("AskMe service obtained")

            # Run the planner asynchronously
            logger.info("Running planner...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                planner_result = loop.run_until_complete(
                    service.plan_questions(intent, session.spec)
                )
                logger.info(f"Planner completed with {len(planner_result.questions)} questions")
            finally:
                loop.close()

            # Store questions in the session
            questions_data = []
            for i, question_spec in enumerate(planner_result.questions):
                question = AskMeQuestion.objects.create(
                    session=session,
                    qid=question_spec.qid,
                    title=question_spec.title,
                    help_text=question_spec.help_text,
                    variable=question_spec.variable,
                    kind=question_spec.kind,
                    options=question_spec.options,
                    is_required=question_spec.required,
                    suggested_answer=question_spec.suggested,
                    order=i
                )
                questions_data.append(question.to_dict())

            # Update session
            session.current_questions = questions_data
            session.good_enough_to_run = planner_result.good_enough_to_run
            session.save()

            logger.info(f"Started AskMe session {session.id} with {len(questions_data)} questions")

            return JsonResponse({
                'session_id': str(session.id),
                'questions': questions_data,
                'good_enough_to_run': planner_result.good_enough_to_run
            })

        except Exception as e:
            logger.error(f"Failed to start AskMe session: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return JsonResponse({
                'error': 'Failed to start session',
                'details': str(e)  # Include error details for debugging
            }, status=500)


class AskMeAnswerView(View):
    """Answer a question in the session"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            # Robust JSON parsing
            raw_body = request.body
            if isinstance(raw_body, bytes):
                raw_body = raw_body.decode('utf-8')
            
            if not raw_body.strip():
                return JsonResponse({
                    'error': 'Request body is empty'
                }, status=400)
            
            try:
                data = json.loads(raw_body)
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON decode error in answer: {json_error}")
                return JsonResponse({
                    'error': 'Invalid JSON format',
                    'details': str(json_error)
                }, status=400)
            
            session_id = data.get('session_id')
            qid = data.get('qid')
            value = data.get('value')

            if not all([session_id, qid, value]):
                return JsonResponse({
                    'error': 'session_id, qid, and value are required'
                }, status=400)

            # Get the session
            try:
                session = AskMeSession.objects.get(id=session_id)
            except AskMeSession.DoesNotExist:
                return JsonResponse({
                    'error': 'Session not found'
                }, status=404)

            # Get the question
            try:
                question = AskMeQuestion.objects.get(session=session, qid=qid)
            except AskMeQuestion.DoesNotExist:
                return JsonResponse({
                    'error': 'Question not found'
                }, status=404)

            # Mark question as answered
            question.mark_answered(value)

            # Get the service and plan next questions
            service = get_askme_service()

            # Run the planner for next questions
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                planner_result = loop.run_until_complete(
                    service.plan_questions(session.intent, session.spec)
                )
            finally:
                loop.close()

            # Update or create new questions
            new_questions_data = []
            for i, question_spec in enumerate(planner_result.questions):
                # Check if question already exists
                existing_question = AskMeQuestion.objects.filter(
                    session=session,
                    qid=question_spec.qid
                ).first()

                if not existing_question:
                    new_question = AskMeQuestion.objects.create(
                        session=session,
                        qid=question_spec.qid,
                        title=question_spec.title,
                        help_text=question_spec.help_text,
                        variable=question_spec.variable,
                        kind=question_spec.kind,
                        options=question_spec.options,
                        is_required=question_spec.required,
                        suggested_answer=question_spec.suggested,
                        order=len(new_questions_data)
                    )
                    new_questions_data.append(new_question.to_dict())
                else:
                    new_questions_data.append(existing_question.to_dict())

            # Generate preview if we're close to done
            preview_prompt = None
            if len(planner_result.questions) < 3:  # Getting close to done
                try:
                    composer_result = loop.run_until_complete(
                        service.compose_prompt(session.spec)
                    )
                    preview_prompt = composer_result.prompt
                    session.preview_prompt = preview_prompt
                except Exception as e:
                    logger.warning(f"Failed to generate preview: {e}")

            # Update session
            session.current_questions = new_questions_data
            session.good_enough_to_run = planner_result.good_enough_to_run
            session.save()

            logger.info(f"Answered question {qid} in session {session_id}")

            return JsonResponse({
                'session_id': str(session.id),
                'questions': new_questions_data,
                'good_enough_to_run': planner_result.good_enough_to_run,
                'preview_prompt': preview_prompt
            })

        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return JsonResponse({
                'error': 'Failed to process answer'
            }, status=500)


class AskMeFinalizeView(View):
    """Generate the final prompt"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            # Robust JSON parsing
            raw_body = request.body
            if isinstance(raw_body, bytes):
                raw_body = raw_body.decode('utf-8')
            
            if not raw_body.strip():
                return JsonResponse({
                    'error': 'Request body is empty'
                }, status=400)
            
            try:
                data = json.loads(raw_body)
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON decode error in finalize: {json_error}")
                return JsonResponse({
                    'error': 'Invalid JSON format',
                    'details': str(json_error)
                }, status=400)
            
            session_id = data.get('session_id')

            if not session_id:
                return JsonResponse({
                    'error': 'session_id is required'
                }, status=400)

            # Get the session
            try:
                session = AskMeSession.objects.get(id=session_id)
            except AskMeSession.DoesNotExist:
                return JsonResponse({
                    'error': 'Session not found'
                }, status=404)

            # Get the service and compose final prompt
            service = get_askme_service()

            # Run the composer
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                composer_result = loop.run_until_complete(
                    service.compose_prompt(session.spec)
                )
            finally:
                loop.close()

            # Update session
            session.final_prompt = composer_result.prompt
            session.is_complete = True
            session.completed_at = datetime.now()
            session.save()

            logger.info(f"Finalized session {session_id}")

            return JsonResponse({
                'prompt': composer_result.prompt,
                'metadata': {
                    'spec': session.spec,
                    'variables_used': list(session.answered_vars.keys()),
                    'completion_percentage': session.get_completion_percentage()
                }
            })

        except Exception as e:
            logger.error(f"Failed to finalize session: {e}")
            return JsonResponse({
                'error': 'Failed to generate final prompt'
            }, status=500)


class AskMeStreamView(View):
    """Stream session updates using Server-Sent Events (SSE)"""

    def get(self, request):
        session_id = request.GET.get('session_id')

        if not session_id:
            return HttpResponse('session_id parameter required', status=400)

        try:
            session = AskMeSession.objects.get(id=session_id)
        except AskMeSession.DoesNotExist:
            return HttpResponse('Session not found', status=404)

        def event_stream():
            """Generate SSE events"""
            try:
                # Send current questions
                for question in session.questions.all():
                    event_data = {
                        'type': 'question',
                        'data': question.to_dict()
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

                # Send preview if available
                if session.preview_prompt:
                    event_data = {
                        'type': 'preview',
                        'data': session.preview_prompt
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

                # Send completion status
                if session.good_enough_to_run:
                    event_data = {
                        'type': 'ready',
                        'data': {'can_finalize': True}
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

                # Send final completion signal
                event_data = {'type': 'complete'}
                yield f"data: {json.dumps(event_data)}\n\n"

            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                error_data = {
                    'type': 'error',
                    'data': {'message': 'Stream error occurred'}
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Cache-Control'

        return response


# API view functions for DRF integration (No auth required for development)
@api_view(['POST'])
@permission_classes([AllowAny])
def askme_start_api(request):
    """DRF API view for starting AskMe session"""
    view = AskMeStartView()
    return view.post(request)

@api_view(['POST'])
@permission_classes([AllowAny])
def askme_answer_api(request):
    """DRF API view for answering questions"""
    view = AskMeAnswerView()
    return view.post(request)

@api_view(['POST'])
@permission_classes([AllowAny])
def askme_finalize_api(request):
    """DRF API view for finalizing session"""
    view = AskMeFinalizeView()
    return view.post(request)

@api_view(['GET'])
@permission_classes([AllowAny])
def askme_stream_api(request):
    """DRF API view for streaming updates"""
    view = AskMeStreamView()
    return view.get(request)

# Session management endpoints (No auth required for development)
@api_view(['GET'])
@permission_classes([AllowAny])
def askme_sessions_list(request):
    """List user's AskMe sessions (all sessions during development)"""
    sessions = AskMeSession.objects.all().order_by('-created_at')[:50]  # Limit to 50 recent sessions
    serializer = AskMeSessionSerializer(sessions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def askme_session_detail(request, session_id):
    """Get session details"""
    try:
        session = AskMeSession.objects.get(id=session_id)
        serializer = AskMeSessionSerializer(session)
        return Response(serializer.data)
    except AskMeSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=404)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def askme_session_delete(request, session_id):
    """Delete a session (no user check during development)"""
    try:
        session = AskMeSession.objects.get(id=session_id)
        session.delete()
        return Response({'message': 'Session deleted'})
    except AskMeSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=404)

# Debug endpoint to test authentication
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def askme_debug_test(request):
    """Debug endpoint to test if authentication is working"""
    return Response({
        'message': 'Ask-Me debug endpoint working!',
        'method': request.method,
        'user': str(request.user) if request.user else 'Anonymous',
        'authenticated': request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else False,
        'headers': dict(request.headers),
        'permissions_working': True
    })
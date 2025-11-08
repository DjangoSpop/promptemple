/**
 * Ask-Me Backend Implementation Guide
 * 
 * This file provides the backend API endpoints and LangChain orchestration
 * for the Ask-Me Prompt Builder system.
 * 
 * SYSTEM ARCHITECTURE:
 * 1. Frontend sends intent → /askme/start
 * 2. Backend creates session + runs Planner to generate first questions
 * 3. Frontend renders questions as animated cards
 * 4. On each answer → /askme/answer triggers Planner + Composer for preview
 * 5. When ready → /askme/finalize calls Composer for final prompt
 * 
 * For Django backend implementation, follow these patterns:
 */

/**
 * DJANGO IMPLEMENTATION EXAMPLE
 * 
 * File: backend/api/views.py
 * 
 * @api_view(['POST'])
 * def askme_start(request):
 *     """Start a new Ask-Me session"""
 *     intent = request.data.get('intent', '')
 *     
 *     session_id = str(uuid.uuid4())
 *     session = {
 *         'session_id': session_id,
 *         'intent': intent,
 *         'spec': {
 *             'goal': '',
 *             'audience': '',
 *             'tone': '',
 *             'style': '',
 *             'context': '',
 *             'constraints': '',
 *             'inputs': {},
 *         },
 *         'answered_vars': {},
 *         'created_at': time.time(),
 *     }
 *     
 *     # Store in cache/database
 *     cache.set(f'askme_{session_id}', session, timeout=3600)
 *     
 *     # Run Planner to get initial questions
 *     from langchain.llms import ChatOpenAI
 *     from langchain.prompts import ChatPromptTemplate
 *     
 *     llm = ChatOpenAI(model='gpt-4o', temperature=0.7)
 *     
 *     planner_prompt = ChatPromptTemplate.from_messages([
 *         ("system", BACKEND_PLANNER_SYSTEM_PROMPT),
 *         ("human", f"Intent: {intent}\n\nSpec: {json.dumps(session['spec'])}")
 *     ])
 *     
 *     planner_chain = planner_prompt | llm
 *     response = planner_chain.invoke({})
 *     
 *     questions = json.loads(response.content)['questions_json']
 *     
 *     return Response({
 *         'session_id': session_id,
 *         'questions': questions,
 *         'good_enough_to_run': len(questions) == 0,
 *     })
 * 
 * 
 * @api_view(['POST'])
 * def askme_answer(request):
 *     """Answer a question in the session"""
 *     session_id = request.data.get('session_id')
 *     qid = request.data.get('qid')
 *     value = request.data.get('value')
 *     
 *     session = cache.get(f'askme_{session_id}')
 *     
 *     # Find the question to get variable name
 *     question = next(q for q in session['questions'] if q['qid'] == qid)
 *     variable = question['variable']
 *     
 *     # Update spec
 *     if variable in ['goal', 'audience', 'tone', 'style', 'context', 'constraints']:
 *         session['spec'][variable] = value
 *     else:
 *         session['spec']['inputs'][variable] = value
 *     
 *     session['answered_vars'][variable] = value
 *     
 *     # Update session
 *     cache.set(f'askme_{session_id}', session)
 *     
 *     # Run Planner for next questions
 *     llm = ChatOpenAI(model='gpt-4o', temperature=0.7)
 *     
 *     planner_prompt = ChatPromptTemplate.from_messages([
 *         ("system", BACKEND_PLANNER_SYSTEM_PROMPT),
 *         ("human", f"Intent: {session['intent']}\n\nSpec: {json.dumps(session['spec'])}")
 *     ])
 *     
 *     planner_chain = planner_prompt | llm
 *     planner_response = planner_chain.invoke({})
 *     questions = json.loads(planner_response.content)['questions_json']
 *     
 *     # Run Composer for preview if enough data
 *     preview_prompt = None
 *     if len(questions) < 3:  # Getting close to done
 *         composer_prompt = ChatPromptTemplate.from_messages([
 *             ("system", BACKEND_COMPOSER_SYSTEM_PROMPT),
 *             ("human", f"Spec: {json.dumps(session['spec'])}")
 *         ])
 *         
 *         composer_chain = composer_prompt | llm
 *         preview_response = composer_chain.invoke({})
 *         preview_prompt = preview_response.content
 *     
 *     session['questions'] = questions
 *     session['preview_prompt'] = preview_prompt
 *     session['good_enough_to_run'] = len(questions) == 0
 *     
 *     cache.set(f'askme_{session_id}', session)
 *     
 *     return Response({
 *         'session_id': session_id,
 *         'questions': questions,
 *         'good_enough_to_run': session['good_enough_to_run'],
 *         'preview_prompt': preview_prompt,
 *     })
 * 
 * 
 * @api_view(['POST'])
 * def askme_finalize(request):
 *     """Generate final prompt"""
 *     session_id = request.data.get('session_id')
 *     session = cache.get(f'askme_{session_id}')
 *     
 *     # Run Composer for final prompt
 *     llm = ChatOpenAI(model='gpt-4o', temperature=0.5)  # Lower temp for consistency
 *     
 *     composer_prompt = ChatPromptTemplate.from_messages([
 *         ("system", BACKEND_COMPOSER_SYSTEM_PROMPT),
 *         ("human", f"Spec: {json.dumps(session['spec'])}")
 *     ])
 *     
 *     composer_chain = composer_prompt | llm
 *     final_response = composer_chain.invoke({})
 *     final_prompt = final_response.content
 *     
 *     session['final_prompt'] = final_prompt
 *     cache.set(f'askme_{session_id}', session)
 *     
 *     return Response({
 *         'prompt': final_prompt,
 *         'metadata': {
 *             'spec': session['spec'],
 *             'variables_used': list(session['answered_vars'].keys()),
 *         }
 *     })
 * 
 * 
 * URL ROUTING (urls.py):
 * 
 * path('api/askme/start', askme_start),
 * path('api/askme/answer', askme_answer),
 * path('api/askme/finalize', askme_finalize),
 * 
 */

export const DJANGO_BACKEND_INSTRUCTIONS = `
Follow the example patterns above to implement in Django with:
- Django REST Framework
- LangChain 
- Redis/Cache for session management
- OpenAI API (or compatible)

Key files to create:
1. backend/api/views.py - Endpoints
2. backend/api/urls.py - Routes
3. backend/api/serializers.py - Request/response validation
`;

/**
 * STREAMING ENDPOINT (Server-Sent Events)
 * 
 * @api_view(['GET'])
 * def askme_stream(request):
 *     """Stream questions and preview updates"""
 *     session_id = request.query_params.get('session_id')
 *     session = cache.get(f'askme_{session_id}')
 *     
 *     def event_stream():
 *         # Send questions as they're generated
 *         for question in session['questions']:
 *             yield f"data: {json.dumps({'type': 'question', 'data': question})}\n\n"
 *         
 *         # Send preview
 *         if session.get('preview_prompt'):
 *             yield f"data: {json.dumps({'type': 'preview', 'data': session['preview_prompt']})}\n\n"
 *         
 *         # Send ready signal
 *         yield f"data: {json.dumps({'type': 'complete'})}\n\n"
 *     
 *     return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
 */

export const STREAMING_IMPLEMENTATION = `
Implement streaming for real-time updates with Server-Sent Events (SSE).
This provides live preview updates as the user fills in answers.
`;

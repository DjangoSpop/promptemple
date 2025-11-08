"""
Views for MVP UI
Server-side rendered Django templates calling backend APIs
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import (
    TemplateCreateForm, TemplateSearchForm, UserLoginForm,
    UserRegistrationForm, UserProfileForm, ResearchJobForm
)
from .api_client import get_api_client
from .middleware import PerformanceTracker
import json


# ============================================
# DASHBOARD & HEALTH
# ============================================

@ensure_csrf_cookie
def dashboard(request):
    """Main dashboard with health checks and metrics"""
    client = get_api_client(request)
    
    # Get health status
    health = client.get('/api/v2/core/health/detailed/')
    
    # Get performance metrics
    tracker = PerformanceTracker.get_instance()
    recent_requests = tracker.get_recent_requests(limit=50)
    endpoint_stats = tracker.get_endpoint_stats()
    
    # Get user stats if authenticated
    user_stats = None
    if request.user.is_authenticated:
        user_stats = client.get('/api/v2/auth/stats/')
    
    context = {
        'health': health,
        'recent_requests': recent_requests,
        'endpoint_stats': endpoint_stats,
        'user_stats': user_stats,
    }
    
    return render(request, 'mvp_ui/dashboard.html', context)


def health_check(request):
    """Health check endpoint"""
    client = get_api_client(request)
    health = client.get('/health/')
    
    if health.get('status') == 'healthy':
        return JsonResponse(health, status=200)
    return JsonResponse(health, status=503)


def metrics(request):
    """Performance metrics endpoint"""
    tracker = PerformanceTracker.get_instance()
    
    return JsonResponse({
        'recent_requests': tracker.get_recent_requests(limit=100),
        'endpoint_stats': tracker.get_endpoint_stats(),
    })


# ============================================
# AUTHENTICATION
# ============================================

@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login page"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            client = get_api_client(request)
            result = client.post('/api/v2/auth/login/', data={
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
            })
            
            if result.get('access'):
                # Store JWT token in cookie
                response = redirect('mvp_ui:dashboard')
                response.set_cookie('jwt-auth', result['access'], httponly=True, samesite='Lax')
                if result.get('refresh'):
                    response.set_cookie('jwt-refresh', result['refresh'], httponly=True, samesite='Lax')
                messages.success(request, 'Login successful!')
                return response
            else:
                messages.error(request, result.get('message', 'Login failed'))
    else:
        form = UserLoginForm()
    
    return render(request, 'mvp_ui/auth/login.html', {'form': form})


def logout_view(request):
    """User logout"""
    response = redirect('mvp_ui:login')
    response.delete_cookie('jwt-auth')
    response.delete_cookie('jwt-refresh')
    messages.success(request, 'Logged out successfully')
    return response


@require_http_methods(["GET", "POST"])
def register_view(request):
    """User registration page"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            client = get_api_client(request)
            result = client.post('/api/v2/auth/register/', data={
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
            })
            
            if result.get('access'):
                # Auto-login after registration
                response = redirect('mvp_ui:dashboard')
                response.set_cookie('jwt-auth', result['access'], httponly=True, samesite='Lax')
                if result.get('refresh'):
                    response.set_cookie('jwt-refresh', result['refresh'], httponly=True, samesite='Lax')
                messages.success(request, 'Registration successful! Welcome!')
                return response
            else:
                messages.error(request, result.get('message', 'Registration failed'))
    else:
        form = UserRegistrationForm()
    
    return render(request, 'mvp_ui/auth/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def profile_view(request):
    """User profile view and edit"""
    client = get_api_client(request)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            result = client.patch('/api/v2/auth/profile/', data=form.cleaned_data)
            
            if result.get('status_code') and result['status_code'] >= 400:
                messages.error(request, result.get('message', 'Update failed'))
            else:
                messages.success(request, 'Profile updated successfully!')
                return redirect('mvp_ui:profile')
    else:
        # Get current profile
        profile_data = client.get('/api/v2/auth/profile/')
        form = UserProfileForm(initial=profile_data if not profile_data.get('status_code') else {})
    
    return render(request, 'mvp_ui/auth/profile.html', {'form': form})


# ============================================
# TEMPLATES
# ============================================

def template_list(request):
    """List templates with search and filters"""
    client = get_api_client(request)
    
    # Build query params from request
    params = {}
    form = TemplateSearchForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('search'):
            params['search'] = form.cleaned_data['search']
        if form.cleaned_data.get('category'):
            params['category'] = form.cleaned_data['category']
        if form.cleaned_data.get('is_public') is not None:
            params['is_public'] = form.cleaned_data['is_public']
        if form.cleaned_data.get('ordering'):
            params['ordering'] = form.cleaned_data['ordering']
    
    # Pagination
    page = request.GET.get('page', 1)
    params['page'] = page
    
    # Fetch templates
    result = client.get('/api/v2/templates/', params=params)
    
    # Fetch categories for filter
    categories = client.get('/api/v2/template-categories/')
    
    context = {
        'form': form,
        'templates': result.get('results', []),
        'pagination': {
            'count': result.get('count', 0),
            'next': result.get('next'),
            'previous': result.get('previous'),
            'current_page': int(page),
        },
        'categories': categories.get('results', []),
    }
    
    return render(request, 'mvp_ui/templates/list.html', context)


def template_detail(request, template_id):
    """Template detail view"""
    client = get_api_client(request)
    
    template = client.get(f'/api/v2/templates/{template_id}/')
    
    if template.get('status_code') and template['status_code'] >= 400:
        messages.error(request, template.get('message', 'Template not found'))
        return redirect('mvp_ui:template_list')
    
    context = {'template': template}
    return render(request, 'mvp_ui/templates/detail.html', context)


@require_http_methods(["GET", "POST"])
def template_create(request):
    """Create new template"""
    client = get_api_client(request)
    
    if request.method == 'POST':
        form = TemplateCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            
            # Convert tags to list
            if data.get('tags'):
                data['tags'] = [tag.strip() for tag in data['tags'].split(',')]
            
            result = client.post('/api/v2/templates/', data=data)
            
            if result.get('id'):
                messages.success(request, 'Template created successfully!')
                return redirect('mvp_ui:template_detail', template_id=result['id'])
            else:
                messages.error(request, result.get('message', 'Failed to create template'))
    else:
        form = TemplateCreateForm()
    
    # Get categories
    categories = client.get('/api/v2/template-categories/')
    
    context = {
        'form': form,
        'categories': categories.get('results', []),
    }
    
    return render(request, 'mvp_ui/templates/create.html', context)


@require_http_methods(["GET", "POST"])
def template_edit(request, template_id):
    """Edit existing template"""
    client = get_api_client(request)
    
    if request.method == 'POST':
        form = TemplateCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            
            # Convert tags to list
            if data.get('tags'):
                data['tags'] = [tag.strip() for tag in data['tags'].split(',')]
            
            result = client.patch(f'/api/v2/templates/{template_id}/', data=data)
            
            if result.get('id'):
                messages.success(request, 'Template updated successfully!')
                return redirect('mvp_ui:template_detail', template_id=result['id'])
            else:
                messages.error(request, result.get('message', 'Failed to update template'))
    else:
        # Get current template data
        template = client.get(f'/api/v2/templates/{template_id}/')
        
        if template.get('status_code') and template['status_code'] >= 400:
            messages.error(request, 'Template not found')
            return redirect('mvp_ui:template_list')
        
        # Convert tags list to comma-separated string for form
        initial_data = template.copy()
        if initial_data.get('tags') and isinstance(initial_data['tags'], list):
            initial_data['tags'] = ', '.join(initial_data['tags'])
        
        form = TemplateCreateForm(initial=initial_data)
    
    # Get categories
    categories = client.get('/api/v2/template-categories/')
    
    context = {
        'form': form,
        'template': template,
        'categories': categories.get('results', []),
    }
    
    return render(request, 'mvp_ui/templates/edit.html', context)


@require_http_methods(["POST"])
def template_delete(request, template_id):
    """Delete template"""
    client = get_api_client(request)
    
    result = client.delete(f'/api/v2/templates/{template_id}/')
    
    if result.get('success') or result.get('status_code') == 204:
        messages.success(request, 'Template deleted successfully')
    else:
        messages.error(request, result.get('message', 'Failed to delete template'))
    
    return redirect('mvp_ui:template_list')


# ============================================
# CATEGORIES
# ============================================

def category_list(request):
    """List template categories"""
    client = get_api_client(request)
    
    page = request.GET.get('page', 1)
    result = client.get('/api/v2/template-categories/', params={'page': page})
    
    context = {
        'categories': result.get('results', []),
        'pagination': {
            'count': result.get('count', 0),
            'next': result.get('next'),
            'previous': result.get('previous'),
            'current_page': int(page),
        },
    }
    
    return render(request, 'mvp_ui/categories/list.html', context)


def category_detail(request, category_id):
    """Category detail with templates"""
    client = get_api_client(request)
    
    category = client.get(f'/api/v2/template-categories/{category_id}/')
    templates = client.get(f'/api/v2/template-categories/{category_id}/templates/')
    
    context = {
        'category': category,
        'templates': templates.get('results', []) if isinstance(templates, dict) else [],
    }
    
    return render(request, 'mvp_ui/categories/detail.html', context)


# ============================================
# RESEARCH
# ============================================

def research_list(request):
    """List research jobs"""
    client = get_api_client(request)
    
    page = request.GET.get('page', 1)
    result = client.get('/api/v2/research/jobs/', params={'page': page})
    
    context = {
        'jobs': result.get('results', []),
        'pagination': {
            'count': result.get('count', 0),
            'next': result.get('next'),
            'previous': result.get('previous'),
            'current_page': int(page),
        },
    }
    
    return render(request, 'mvp_ui/research/list.html', context)


@require_http_methods(["GET", "POST"])
def research_create(request):
    """Create new research job"""
    client = get_api_client(request)
    
    if request.method == 'POST':
        form = ResearchJobForm(request.POST)
        if form.is_valid():
            result = client.post('/api/v2/research/jobs/', data=form.cleaned_data)
            
            if result.get('id'):
                messages.success(request, 'Research job created successfully!')
                return redirect('mvp_ui:research_detail', job_id=result['id'])
            else:
                messages.error(request, result.get('message', 'Failed to create research job'))
    else:
        form = ResearchJobForm()
    
    return render(request, 'mvp_ui/research/create.html', {'form': form})


def research_detail(request, job_id):
    """Research job detail with progress"""
    client = get_api_client(request)
    
    job = client.get(f'/api/v2/research/jobs/{job_id}/')
    
    if job.get('status_code') and job['status_code'] >= 400:
        messages.error(request, 'Research job not found')
        return redirect('mvp_ui:research_list')
    
    # Get progress
    progress = client.get(f'/api/v2/research/jobs/{job_id}/progress/')
    
    context = {
        'job': job,
        'progress': progress if not progress.get('status_code') else {},
    }
    
    return render(request, 'mvp_ui/research/detail.html', context)


# ============================================
# SSE DEMO
# ============================================

def sse_demo(request):
    """SSE streaming demo page"""
    return render(request, 'mvp_ui/sse/demo.html')


def sse_test(request):
    """SSE test endpoint - streams server-sent events"""
    import time
    
    def event_stream():
        """Generate SSE events"""
        for i in range(10):
            data = json.dumps({
                'id': i,
                'message': f'Test event {i}',
                'timestamp': time.time(),
            })
            yield f"data: {data}\n\n"
            time.sleep(1)
        
        yield "data: [DONE]\n\n"
    
    response = HttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ============================================
# AI SERVICES
# ============================================

def ai_providers(request):
    """List AI providers and models"""
    client = get_api_client(request)
    
    providers = client.get('/api/v2/ai/providers/')
    models = client.get('/api/v2/ai/models/')
    
    context = {
        'providers': providers.get('providers', []) if isinstance(providers, dict) else [],
        'models': models.get('models', []) if isinstance(models, dict) else [],
    }
    
    return render(request, 'mvp_ui/ai/providers.html', context)


def ai_chat(request):
    """AI chat interface"""
    return render(request, 'mvp_ui/ai/chat.html')

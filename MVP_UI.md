📍 MVP UI URLs
Main Dashboard & Health
Dashboard: http://127.0.0.1:8000/mvp-ui/
Health Check: http://127.0.0.1:8000/mvp-ui/health/
Performance Metrics: http://127.0.0.1:8000/mvp-ui/metrics/
Authentication
Login: http://127.0.0.1:8000/mvp-ui/auth/login/
Register: http://127.0.0.1:8000/mvp-ui/auth/register/
Logout: http://127.0.0.1:8000/mvp-ui/auth/logout/
Profile: http://127.0.0.1:8000/mvp-ui/auth/profile/
Templates
Template List: http://127.0.0.1:8000/mvp-ui/templates/
Create Template: http://127.0.0.1:8000/mvp-ui/templates/create/
Template Detail: http://127.0.0.1:8000/mvp-ui/templates/<uuid>/ (replace <uuid> with actual template ID)
Edit Template: http://127.0.0.1:8000/mvp-ui/templates/<uuid>/edit/
Delete Template: http://127.0.0.1:8000/mvp-ui/templates/<uuid>/delete/ (POST only)
Categories
Category List: http://127.0.0.1:8000/mvp-ui/categories/
Category Detail: http://127.0.0.1:8000/mvp-ui/categories/<id>/ (replace <id> with category ID)
Research
Research Jobs List: http://127.0.0.1:8000/mvp-ui/research/
Create Research Job: http://127.0.0.1:8000/mvp-ui/research/create/
Research Job Detail: http://127.0.0.1:8000/mvp-ui/research/<uuid>/
SSE Demo
SSE Demo Page: http://127.0.0.1:8000/mvp-ui/sse/demo/
SSE Test Endpoint (for EventSource): http://127.0.0.1:8000/mvp-ui/sse/test/
AI Services
AI Providers: http://127.0.0.1:8000/mvp-ui/ai/providers/
AI Chat: http://127.0.0.1:8000/mvp-ui/ai/chat/
🚀 Quick Start Command

python manage.py runserver
Then navigate to: http://127.0.0.1:8000/mvp-ui/

🔗 Navigation Flow
The navigation bar (in base.html) provides links to all these pages:

Dashboard → Main landing page with health & metrics
Templates → Browse, create, edit templates
Categories → Browse by category
Research → Research job management
SSE Demo → Test server-sent events
AI Services → AI providers and models
Login/Register (if not authenticated)
Profile/Logout (if authenticated)
All pages use Bootstrap 5 styling and are fully responsive! 🎨
# 🚀 QUICK START GUIDE - Lean PromptCraft Backend

## ✅ What's Been Done

1. **requirements-lean.txt** - Optimized dependencies (~200MB)
2. **Prompt Enhancement Service** - Direct DeepSeek API integration
3. **Complete Documentation** - 7-sprint implementation plan
4. **Test Suite** - Validation scripts

---

## 🎯 Next Steps (In Order)

### STEP 1: Test the Current Service (5 minutes)

```powershell
# Test the prompt enhancement service
python test_prompt_enhancer.py
```

**Expected:** All basic tests should pass ✅

---

### STEP 2: Install Lean Dependencies (10 minutes)

```powershell
# Create new virtual environment (recommended)
python -m venv venv_lean
.\venv_lean\Scripts\activate

# Install lean requirements
pip install -r requirements-lean.txt

# Verify installation
pip list | Select-String "Django"
```

**Expected:** ~25-30 packages installed (not 60+)

---

### STEP 3: Update Billing Models (15 minutes)

**File to create/update:** `apps/billing/models.py`

Copy the code from `LEAN_RESCUE_PLAN.md` → Sprint 4 → Task 4.1

Key models:
- `UsageStats` - Track enhancements per month
- `UserProfile` - User tier and limits

```powershell
# After updating models:
python manage.py makemigrations billing
python manage.py migrate billing
```

---

### STEP 4: Create API Views (30 minutes)

**File to create/update:** `apps/ai_services/views.py`

Copy the code from `LEAN_RESCUE_PLAN.md` → Sprint 3 → Task 3.1

Key views:
- `PromptEnhancementView` - POST /api/v2/ai/enhance
- `get_prompt_history` - GET /api/v2/ai/history

**Update URLs:**

`apps/ai_services/urls.py`:
```python
from django.urls import path
from . import views

app_name = 'ai_services'

urlpatterns = [
    path('enhance', views.PromptEnhancementView.as_view(), name='enhance'),
    path('history', views.get_prompt_history, name='history'),
]
```

`promptcraft/urls.py` - Add:
```python
path('api/v2/ai/', include('apps.ai_services.urls')),
```

---

### STEP 5: Test the API (10 minutes)

```powershell
# Start server
python manage.py runserver

# In another terminal, test with curl:
curl -X POST http://localhost:8000/api/v2/ai/enhance `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"prompt":"write a blog post","enhancement_type":"general"}'
```

**Expected:** JSON response with enhanced prompt

---

### STEP 6: Create Dockerfile (20 minutes)

Copy `Dockerfile.lean` from `LEAN_RESCUE_PLAN.md` → Sprint 6 → Task 6.1

```powershell
# Build image
docker build -f Dockerfile.lean -t promptcraft:lean .

# Check size
docker images | Select-String "promptcraft"
```

**Expected:** Image size <400MB

---

### STEP 7: Test with Docker Compose (15 minutes)

Copy `docker-compose.lean.yml` from `LEAN_RESCUE_PLAN.md` → Sprint 6 → Task 6.1

```powershell
# Start all services
docker-compose -f docker-compose.lean.yml up -d

# Check health
curl http://localhost:8000/api/v2/health/

# View logs
docker-compose -f docker-compose.lean.yml logs -f backend
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `LEAN_RESCUE_PLAN.md` | **Complete 7-sprint guide** - Your main reference |
| `IMPLEMENTATION_PROGRESS.md` | Current status and next steps |
| `requirements-lean.txt` | Optimized dependencies |
| `test_prompt_enhancer.py` | Service validation tests |
| `apps/ai_services/services/prompt_enhancer.py` | Lean enhancement service |

---

## 🔍 Troubleshooting

### Issue: Module not found
```powershell
# Make sure you're in the right virtual environment
pip list | Select-String "Django"

# Reinstall if needed
pip install -r requirements-lean.txt
```

### Issue: Database errors
```powershell
# Run migrations
python manage.py migrate

# Reset if needed
python manage.py migrate --run-syncdb
```

### Issue: DEEPSEEK_API_KEY not found
```env
# Add to .env file:
DEEPSEEK_API_KEY=your-actual-key-here
```

### Issue: Import errors in views.py
```python
# Make sure these imports work:
from apps.ai_services.services.prompt_enhancer import (
    PromptEnhancerService, 
    PromptEnhancementError
)
from apps.billing.models import UsageStats
```

---

## ✅ Success Checklist

- [ ] Test script passes (`python test_prompt_enhancer.py`)
- [ ] Lean dependencies installed (<30 packages)
- [ ] Billing models created and migrated
- [ ] API views implemented
- [ ] API endpoint responds correctly
- [ ] Docker image builds (<400MB)
- [ ] Docker Compose runs successfully
- [ ] Health check returns OK

---

## 🎯 Final Goal

A working, lean backend with:
- ✅ Prompt enhancement API
- ✅ Usage tracking and rate limiting
- ✅ Prompt history
- ✅ Docker deployment ready
- ✅ <400MB image size
- ✅ <200ms API response time

---

## 📞 Where to Get Help

1. **LEAN_RESCUE_PLAN.md** - Detailed implementation for each sprint
2. **IMPLEMENTATION_PROGRESS.md** - Current status and what's done
3. **Test script errors** - Run `python test_prompt_enhancer.py` for diagnostics

---

**Estimated Total Time:** 2-3 hours for complete Sprint 2 implementation

**Priority Order:**
1. Test current service ✅ (Already done)
2. Install dependencies (10 min)
3. Update billing models (15 min)
4. Create API views (30 min)
5. Test API (10 min)
6. Docker setup (35 min)

**Start with Step 2** if you haven't installed lean dependencies yet!

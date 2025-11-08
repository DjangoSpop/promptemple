# 🚨 CORS Fix - Quick Reference Card

## Problem
CORS headers NOT returned despite correct configuration

## Root Cause
Django was loading old `settings.py` file instead of `settings/` package

## Solution (✅ APPLIED)
Updated `manage.py`, `asgi.py`, `wsgi.py` to use environment-based settings

## 🔑 CRITICAL: Environment Variable Required!

### Windows PowerShell:
```powershell
$env:DJANGO_ENVIRONMENT="development"
python manage.py runserver 0.0.0.0:8000
```

### Linux/macOS:
```bash
export DJANGO_ENVIRONMENT=development
python manage.py runserver 0.0.0.0:8000
```

## ✅ Verification (3 Steps)

### 1. Test CORS Headers
```bash
curl -X OPTIONS http://127.0.0.1:8000/api/v2/templates/ \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v
```
**Expected**: `Access-Control-Allow-Origin: http://localhost:3001` ✓

### 2. Run Verification Command
```bash
export DJANGO_ENVIRONMENT=development
python manage.py verify_api --check-cors --verbose
```
**Expected**: All endpoints show `✓ CORS enabled`

### 3. Test Frontend
```bash
# Terminal 1
export DJANGO_ENVIRONMENT=development
python manage.py runserver 0.0.0.0:8000

# Terminal 2
cd ../my_prmpt_frontend
npm start

# Browser: http://localhost:3001
# Console (F12): NO CORS errors ✓
```

## 📋 Files Modified
- ✅ `manage.py`
- ✅ `asgi.py`
- ✅ `wsgi.py`

## 📂 Settings Structure
```
promptcraft/settings/
├── __init__.py          ← Selects which settings to load
├── base.py              ← Shared (CORS middleware setup)
├── development.py       ← DEBUG=True, CORS_ALLOW_ALL_ORIGINS=True
├── production.py        ← DEBUG=False, specific CORS domains
└── testing.py
```

## 🎯 Environment Variable
| Value | Settings File | Use Case |
|-------|---------------|----------|
| `development` | `settings/development.py` | Local dev (DEBUG=True) |
| `production` | `settings/production.py` | Production deployment |
| `testing` | `settings/testing.py` | Unit tests |

Default: `development` (if not set)

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Still seeing CORS errors | Set env var: `export DJANGO_ENVIRONMENT=development` |
| Can't find environment variable | Restart terminal after setting it |
| Getting 401 errors | That's AUTH not CORS - you need to login |
| Getting HTML response | Backend error - check terminal for traceback |

## 📚 Documentation
- **CRITICAL_CORS_FIX_INSTRUCTIONS.md** - Detailed fix (start here!)
- **CORS_FIX_GUIDE.md** - Technical deep dive
- **FIX_SUMMARY.md** - This fix explained
- **FRONTEND_DEBUGGING_GUIDE.md** - Debugging guide
- **API_INTEGRATION_GUIDE.md** - API reference

## ✨ Expected Outcome
```
Frontend (localhost:3001) → CORS headers allowed → Backend (127.0.0.1:8000)
                                ↓
                  NO MORE CORS ERRORS ✅
```

## 🚀 Next Steps
1. Set `DJANGO_ENVIRONMENT=development`
2. Restart backend
3. Test with curl command above
4. Start frontend
5. Open http://localhost:3001
6. Check browser console - should be clean! ✓

---

**For detailed instructions**: Read [CRITICAL_CORS_FIX_INSTRUCTIONS.md](./CRITICAL_CORS_FIX_INSTRUCTIONS.md)  
**For technical details**: Read [CORS_FIX_GUIDE.md](./CORS_FIX_GUIDE.md)

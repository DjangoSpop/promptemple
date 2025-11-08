# PromptCraft Quick Reference Card

## 🚀 Start Backend (5 seconds)

```bash
cd my_prmpt_backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows
python manage.py runserver 0.0.0.0:8000
```

## 🚀 Start Frontend (5 seconds)

```bash
cd my_prmpt_frontend
npm start  # Runs on http://localhost:3001
```

## ✅ Verify Everything Works

```bash
# Backend
curl http://127.0.0.1:8000/health/

# CORS
python manage.py verify_api --check-cors

# Frontend should load without console errors
```

---

## 📚 Key Documentation

| Need | File | Link |
|------|------|------|
| Frontend integration | `API_INTEGRATION_GUIDE.md` | [Read](./API_INTEGRATION_GUIDE.md) |
| Setup instructions | `ENVIRONMENT_SETUP_GUIDE.md` | [Read](./ENVIRONMENT_SETUP_GUIDE.md) |
| Debug issues | `FRONTEND_DEBUGGING_GUIDE.md` | [Read](./FRONTEND_DEBUGGING_GUIDE.md) |
| Authentication | `AUTHENTICATION_GUIDE.md` | [Read](./AUTHENTICATION_GUIDE.md) |
| API reference | `API_COVERAGE.md` | [Read](./API_COVERAGE.md) |
| Deployment | `RAILWAY_DEPLOYMENT.md` | [Read](./RAILWAY_DEPLOYMENT.md) |
| Copy to frontend | `FRONTEND_API_CLIENT.ts` | [Copy](./FRONTEND_API_CLIENT.ts) |

---

## 🔧 Common Commands

### Backend Commands

```bash
# Migrations
python manage.py migrate                 # Apply migrations
python manage.py makemigrations          # Create migrations
python manage.py showmigrations          # List migrations

# Database
python manage.py shell                   # Interactive shell
python manage.py dbshell                 # Database shell
python manage.py flush                   # Clear database

# Testing
python manage.py test                    # Run all tests
python manage.py test apps.templates     # Run app tests

# Users
python manage.py createsuperuser         # Create admin user
python manage.py changepassword <user>   # Change password

# Tools
python manage.py verify_api --check-cors # Verify endpoints
python manage.py runserver               # Start development server
python manage.py collectstatic           # Collect static files
```

### Frontend Commands

```bash
npm install                  # Install dependencies
npm start                    # Start dev server (localhost:3001)
npm run build                # Build for production
npm test                     # Run tests
npm run lint                 # Check code style
npm run format               # Format code
```

---

## 🌐 Key URLs

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/health/` | GET | ❌ | Health check |
| `/api/v2/auth/login/` | POST | ❌ | Login |
| `/api/v2/auth/register/` | POST | ❌ | Register |
| `/api/v2/core/config/` | GET | ✅ | App config |
| `/api/v2/templates/` | GET | ✅ | List templates |
| `/api/v2/ai/assistant/` | GET/POST | ✅ | AI assistant |
| `/api/v2/analytics/dashboard/` | GET | ✅ | Analytics |
| `/api/schema/swagger-ui/` | GET | ❌ | API docs |

**Full list:** See [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md#api-endpoints)

---

## 🔐 Environment Variables

### Development (.env)

```env
DEBUG=True
SECRET_KEY=dev-secret
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
API_DOMAIN=http://127.0.0.1:8000
FRONTEND_DOMAIN=http://localhost:3001
```

### Production (.env)

```env
DEBUG=False
SECRET_KEY=<generate-secure-key>
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379/0
API_DOMAIN=https://api.prompt-temple.com
FRONTEND_DOMAIN=https://www.prompt-temple.com
SENTRY_DSN=<sentry-dsn>
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| CORS error | Run: `python manage.py verify_api --check-cors` |
| 401 unauthorized | Check token: `localStorage.getItem('accessToken')` |
| 404 not found | Verify URL: `/api/v2/` (not `/api/v1/`) |
| Timeout error | Check backend is running: `curl http://127.0.0.1:8000/health/` |
| Database error | Run migrations: `python manage.py migrate` |
| Static files missing | Collect them: `python manage.py collectstatic` |

**Full guide:** See [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md)

---

## 📦 Dependencies

### Backend (Python)
- Django 4.0+
- djangorestframework (DRF)
- django-cors-headers
- djangorestframework-simplejwt
- channels (WebSocket)
- celery (Tasks)
- redis (Caching)
- psycopg2 (PostgreSQL)

### Frontend (Node.js)
- React 18+
- TypeScript
- Axios
- TanStack Query (React Query)
- Tailwind CSS (or your CSS framework)

---

## 🚀 Deployment (Quick Version)

### Railway (Easiest)

```bash
# 1. Push to GitHub
git push origin main

# 2. Connect Railway to repo
# See: https://railway.app/

# 3. Set env vars in Railway dashboard
# 4. Done! Railway auto-deploys
```

### Other Platforms

- **AWS:** See [ENVIRONMENT_SETUP_GUIDE.md](./ENVIRONMENT_SETUP_GUIDE.md)
- **Heroku:** See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
- **DigitalOcean:** See [ENVIRONMENT_SETUP_GUIDE.md](./ENVIRONMENT_SETUP_GUIDE.md)
- **Custom Server:** See [ENVIRONMENT_SETUP_GUIDE.md](./ENVIRONMENT_SETUP_GUIDE.md)

---

## 🔒 Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] HTTPS/SSL configured
- [ ] CORS restricted to known domains
- [ ] JWT tokens using HS256 or RS256
- [ ] Secrets not in version control
- [ ] Database backups configured
- [ ] Error monitoring (Sentry) set up
- [ ] Rate limiting enabled
- [ ] CSRF protection enabled

---

## 📞 Need Help?

1. **Check console** → F12 → Console tab for errors
2. **Check Network tab** → F12 → Network for request details
3. **Check backend logs** → Terminal where server is running
4. **Run verification** → `python manage.py verify_api --check-cors`
5. **Read docs** → See [📚 Key Documentation](#-key-documentation) above
6. **Search issue** → Ctrl+F in relevant documentation file

---

## 📄 File Locations

```
Backend:
  /API_INTEGRATION_GUIDE.md          ← Frontend integration
  /ENVIRONMENT_SETUP_GUIDE.md        ← Setup & deployment
  /FRONTEND_API_CLIENT.ts            ← TypeScript client (copy to frontend)
  /FRONTEND_DEBUGGING_GUIDE.md       ← Debugging guide
  /AUTHENTICATION_GUIDE.md           ← Auth details
  /API_COVERAGE.md                   ← Endpoint status
  /RAILWAY_DEPLOYMENT.md             ← Railway deployment
  /README_INTEGRATION.md             ← Main readme (this repo)
  /README_QUICK_REFERENCE.md         ← This file
  
Backend Code:
  /promptcraft/settings.py           ← Django config
  /promptcraft/urls.py               ← URL routes
  /apps/*/views.py                   ← Endpoint handlers
  /apps/*/models.py                  ← Database models
  /apps/*/serializers.py             ← API serializers
```

---

## 🎯 Checklist: First Time Setup

- [ ] Clone backend: `git clone <url> my_prmpt_backend`
- [ ] Clone frontend: `git clone <url> my_prmpt_frontend`
- [ ] Create Python venv: `python -m venv venv`
- [ ] Install backend deps: `pip install -r requirements.txt`
- [ ] Create `.env` file with `DEBUG=True`
- [ ] Run migrations: `python manage.py migrate`
- [ ] Start backend: `python manage.py runserver 0.0.0.0:8000`
- [ ] Install frontend deps: `npm install`
- [ ] Start frontend: `npm start`
- [ ] Verify no console errors
- [ ] Run verification: `python manage.py verify_api --check-cors`
- [ ] You're done! 🎉

---

## 🎓 Learning Path

1. **Day 1:** Read [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)
2. **Day 1:** Run Quick Start above
3. **Day 2:** Read [ENVIRONMENT_SETUP_GUIDE.md](./ENVIRONMENT_SETUP_GUIDE.md)
4. **Day 2:** Copy `FRONTEND_API_CLIENT.ts` to frontend
5. **Day 3:** Integrate API client into frontend
6. **Day 3:** Test login/logout flow
7. **Day 4:** Implement data loading
8. **When stuck:** See [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md)
9. **Ready to deploy:** See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

---

**Last Updated:** October 28, 2025  
**Version:** 1.0.0  

👉 **Start here:** [README_INTEGRATION.md](./README_INTEGRATION.md)

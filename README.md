<div align="center">

# 🌍 DisasterWatch

### A multi-hazard monitoring platform — currently tracking global earthquakes (mag ≥ 6.0) via USGS API. Weather & flood monitoring coming soon.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Built--in-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.14-red?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<br/>

![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen?style=flat-square)
![Phase](https://img.shields.io/badge/Phase-1_Earthquake_Monitoring-orange?style=flat-square)
![Coming Soon](https://img.shields.io/badge/Coming_Soon-Weather_|_Floods_|_Wildfires-blue?style=flat-square)
![USGS API](https://img.shields.io/badge/Data_Source-USGS_Earthquake_API-orange?style=flat-square)
![Auth](https://img.shields.io/badge/Auth-Custom_Session_Based-blue?style=flat-square)

</div>

---

## 📌 About The Project

**DisasterWatch** is a full-stack Django web application built to monitor global natural disasters. In **Phase 1**, it integrates with the **USGS Earthquake Hazards Program API** to fetch, filter, and persist significant earthquake data — displaying it through a sleek dark-themed dashboard and exposing it via a fully documented **REST API**.

---

## ✨ Features

### 🔐 Authentication System
- Custom login & registration (no Django built-in auth)
- SHA-256 password hashing with salt
- Session-based access control
- All pages protected — unauthenticated users redirected to login

### 📡 USGS Data Integration
- Fetches earthquake data from the official [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/)
- User selects **Start Date** and **End Date** dynamically via form
- Filters only earthquakes with **magnitude ≥ 6.0**
- Stores: ID, magnitude, place, time, latitude, longitude, depth, URL
- Prevents duplicate entries using USGS earthquake ID as primary key

### 📊 Dashboard
- Total earthquakes, strongest quake, latest event, total users
- Magnitude distribution bar chart (Chart.js)
- Recent 5 earthquakes table

### 🗂️ Earthquake Records Page
- Full paginated table (25 per page)
- Search, filter by magnitude/date, sort by multiple columns
- Color-coded magnitude pills, direct USGS event links

### 🔌 REST API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/earthquakes/` | List all earthquakes (paginated, filterable) |
| GET | `/api/earthquakes/<id>/` | Single earthquake by USGS ID |
| POST | `/api/fetch/` | Trigger USGS data fetch with date range |
| GET | `/api/dashboard/stats/` | Aggregate statistics in JSON |
| GET | `/api/users/` | List all users (no passwords exposed) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Django 4.2 |
| REST API | Django REST Framework |
| Database | SQLite (built-in, zero setup) |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Charts | Chart.js |
| Data Source | USGS Earthquake Hazards API |

---

## 📁 Project Structure

```
disaster-watch/
│
├── manage.py
├── requirements.txt
├── db.sqlite3                       # Auto-created on first migration
│
├── earthquake_project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── earthquake_app/
│   ├── models.py
│   ├── views.py
│   ├── api_views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── api_urls.py
│   ├── forms.py
│   ├── usgs_fetcher.py
│   └── migrations/
│
└── templates/
    └── earthquake_app/
        ├── base.html
        ├── login.html
        ├── register.html
        ├── dashboard.html
        ├── earthquakes.html
        └── fetch.html
```

---

## ⚙️ Local Development Setup

### Prerequisites
- Python 3.10+
- pip

> ✅ **No database setup needed** — SQLite is built into Python.

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/your-username/disaster-watch.git
cd disaster-watch

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py makemigrations earthquake_app
python manage.py migrate

# 5. Start server
python manage.py runserver
```

Open `http://127.0.0.1:8000/` → Register → Login → Fetch Data ✅

---

## 🚀 Deployment Guide (Production)

> ⚠️ **Never deploy with development settings.**
> Follow every step below before making this project public.

---

### Step 1 — Create a `.env` file for secrets

Never hardcode secrets in `settings.py`. Create a `.env` file in the root:

```env
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

Install `python-decouple` to read `.env`:

```bash
pip install python-decouple
```

Update `settings.py`:

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')
```

---

### Step 2 — Generate a strong SECRET_KEY

Run this in Python shell and paste the output into `.env`:

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> ❌ Never use the default key from `settings.py` in production.
> ❌ Never commit `.env` to GitHub.

---

### Step 3 — Add `.env` and `db.sqlite3` to `.gitignore`

Create or update `.gitignore` in your project root:

```gitignore
# Environment variables — NEVER commit these
.env
.env.*

# SQLite database — contains real user data
db.sqlite3

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Virtual environment
venv/
env/
.venv/

# Django
*.log
local_settings.py
staticfiles/
media/

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

---

### Step 4 — Set DEBUG = False

```python
# settings.py
DEBUG = False   # ← MUST be False in production
```

> With `DEBUG=True`, Django shows full error pages with your **code, file paths,
> and environment variables** to anyone who triggers an error. This is a critical
> security leak in production.

---

### Step 5 — Lock down ALLOWED_HOSTS

```python
# settings.py — only your actual domain
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

> ❌ Never use `ALLOWED_HOSTS = ['*']` in production.
> This allows HTTP Host header attacks.

---

### Step 6 — Add Security Middleware settings

Add these to the bottom of `settings.py`:

```python
# ── Production Security Settings ──────────────────────────────────────────

# Force all traffic over HTTPS
SECURE_SSL_REDIRECT = True

# HSTS: tell browsers to always use HTTPS for 1 year
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Prevent browsers from guessing content types
SECURE_CONTENT_TYPE_NOSNIFF = True

# Block XSS in older browsers
SECURE_BROWSER_XSS_FILTER = True

# Prevent clickjacking — only allow your domain in iframes
X_FRAME_OPTIONS = 'DENY'

# Session cookie only sent over HTTPS
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True    # JavaScript cannot access session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection for cookies

# CSRF cookie only sent over HTTPS
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Logout user after 1 hour of inactivity
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

---

### Step 7 — Collect static files

```bash
python manage.py collectstatic
```

Add to `settings.py`:

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

---

### Step 8 — Use Gunicorn (not Django dev server)

```bash
pip install gunicorn
gunicorn earthquake_project.wsgi:application --bind 0.0.0.0:8000
```

> ❌ `python manage.py runserver` is for development only — it is
> single-threaded and not secure for production.

---

### Step 9 — Set up Nginx as reverse proxy

Example `/etc/nginx/sites-available/disasterwatch`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }
}
```

---

### Step 10 — Get a free SSL certificate (HTTPS)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

> ✅ HTTPS is **mandatory** for any deployed web app.
> Without it, passwords and session tokens travel in plain text over the network.

---

## 🔒 Security Checklist

Before going live, verify every item below:

```
DEPLOYMENT SECURITY CHECKLIST
──────────────────────────────────────────────────────────────────

SECRET & CONFIG
  [ ] SECRET_KEY is long, random, unique — not the default from settings.py
  [ ] SECRET_KEY is stored in .env — not hardcoded in settings.py
  [ ] .env file is in .gitignore — not pushed to GitHub
  [ ] db.sqlite3 is in .gitignore — not pushed to GitHub
  [ ] DEBUG = False in production settings

NETWORK & HTTPS
  [ ] ALLOWED_HOSTS lists only your actual domain — no '*'
  [ ] HTTPS is enabled with a valid SSL certificate (Let's Encrypt)
  [ ] SECURE_SSL_REDIRECT = True — HTTP auto-redirects to HTTPS
  [ ] HSTS headers configured (SECURE_HSTS_SECONDS = 31536000)
  [ ] Nginx or Apache configured as reverse proxy

COOKIES & SESSIONS
  [ ] SESSION_COOKIE_SECURE = True
  [ ] SESSION_COOKIE_HTTPONLY = True
  [ ] CSRF_COOKIE_SECURE = True
  [ ] SESSION_COOKIE_AGE set (e.g. 3600 = 1 hour timeout)

HEADERS & CONTENT
  [ ] X_FRAME_OPTIONS = 'DENY' (clickjacking protection)
  [ ] SECURE_CONTENT_TYPE_NOSNIFF = True
  [ ] SECURE_BROWSER_XSS_FILTER = True

SERVER
  [ ] Running Gunicorn — not manage.py runserver
  [ ] Static files collected with collectstatic
  [ ] Gunicorn running as non-root user
  [ ] Firewall configured (only ports 80, 443, 22 open)
```

---

## ⚠️ What NOT to Push to GitHub

```
NEVER COMMIT THESE FILES
─────────────────────────────────────────────────
  ❌  .env                  (contains SECRET_KEY, passwords)
  ❌  db.sqlite3            (contains real user data)
  ❌  local_settings.py     (may contain credentials)
  ❌  *.log                 (may contain sensitive request data)
  ❌  staticfiles/          (generated — not source code)
  ❌  venv/ or env/         (virtual environment — huge, not needed)
```

If you accidentally pushed any of these:

```bash
# Remove from git tracking but keep the file locally
git rm --cached .env
git rm --cached db.sqlite3
git commit -m "Remove sensitive files from tracking"
git push

# Then immediately rotate your SECRET_KEY — treat it as compromised
```

---

## 🔌 REST API Reference

### GET /api/earthquakes/

**Query params:** `search`, `mag_min`, `mag_max`, `date_from`, `date_to`, `sort`, `page`, `page_size`

```json
{
  "count": 254,
  "next": "http://yourdomain.com/api/earthquakes/?page=2",
  "previous": null,
  "results": [
    {
      "earthquake_id": "us7000mfgl",
      "magnitude": "7.50",
      "place": "Tonga region",
      "time": "2024-01-15T08:22:14Z",
      "latitude": "-20.123456",
      "longitude": "-174.567890",
      "depth": "35.000",
      "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000mfgl",
      "fetched_at": "2024-03-16T10:00:00Z"
    }
  ]
}
```

### POST /api/fetch/

```json
// Request
{ "start_date": "2024-01-01", "end_date": "2024-01-31" }

// Response
{
  "message": "Fetch complete.",
  "fetched": 1842,
  "filtered": 47,
  "inserted": 45,
  "skipped": 2,
  "errors": []
}
```

### GET /api/dashboard/stats/

```json
{
  "total_earthquakes": 254,
  "total_users": 3,
  "strongest_mag": 8.1,
  "strongest_place": "Tonga region",
  "latest_time": "2024-03-15T14:22:00Z",
  "latest_place": "Near the east coast of Honshu, Japan",
  "last_fetch": "2024-03-16T08:00:00Z"
}
```

---

## 📦 requirements.txt

```
Django>=4.2,<5.0
djangorestframework>=3.14
requests>=2.31
python-decouple>=3.8
gunicorn>=21.2
```

> ✅ SQLite is built into Python — no extra database driver needed.

---

## 🗺️ Roadmap

### ✅ Phase 1 — Earthquake Monitoring (Current)
- [x] USGS Earthquake API integration
- [x] Magnitude ≥ 6.0 filtering
- [x] SQLite persistent storage
- [x] Custom user authentication (SHA-256 hashed passwords)
- [x] Interactive dashboard with Chart.js
- [x] REST API (GET + POST endpoints)
- [x] Search, filter, sort, pagination

### 🔄 Phase 2 — Weather Monitoring (Upcoming)
- [ ] OpenWeatherMap API integration
- [ ] Real-time temperature, humidity, wind data
- [ ] Severe weather alerts
- [ ] City-wise weather dashboard

### 🔄 Phase 3 — Flood & Natural Disaster Tracking (Planned)
- [ ] Flood warning API integration
- [ ] River level monitoring
- [ ] Disaster heatmap visualization
- [ ] Email/SMS alert system

### 🔄 Phase 4 — Unified Alert System (Future)
- [ ] All disasters on one map
- [ ] User location-based notifications
- [ ] Historical data comparison
- [ ] Mobile responsive PWA

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/) — free public API
- [Django](https://www.djangoproject.com/) — web framework
- [Django REST Framework](https://www.django-rest-framework.org/) — REST API layer
- [Bootstrap 5](https://getbootstrap.com/) — responsive UI
- [Chart.js](https://www.chartjs.org/) — magnitude distribution chart

---

<div align="center">

Made with ❤️ | Data powered by USGS Earthquake API

⭐ **Star this repo if you found it useful!** ⭐

</div>

# 🚀 FastAPI Backend Project Setup

This project is a scalable FastAPI backend built with best practices using:

- `venv` for isolated Python environments
- `Poetry` for dependency management
- `run.py` for cross-platform development startup

---

## 🖥️ Local Development Setup

### 1. Clone the Repository

> ✅ If you're setting up the project for use or deployment, **clone the main repository**.  
> 🔁 If you're contributing, please follow the instructions in [CONTRIBUTING.md](./CONTRIBUTING.md) instead.

```bash
git clone https://github.com/your-org-or-username/your-repo-name.git
cd your-repo-name
```

---

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv env

# Activate it
# macOS/Linux:
source env/bin/activate

# Windows:
env\Scripts\Activate
```

---

### 3. Install Poetry

Install Poetry globally if you don't have it already:

```bash
pip install poetry
```

Check the installation:

```bash
poetry --version
```

---

### 4. Install Project Dependencies

Use Poetry to install the project’s dependencies:

```bash
poetry install
```

---

### 5. Run the Development Server

Use the `run.py` script to start the FastAPI app:

```bash
poetry run python run.py
```

Once started, the app will be available at:  
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🛡️ Creating a Superadmin User

To set up an initial superadmin account for your project, follow the step-by-step instructions in [CREATE_SUPERADMIN.md](./CREATE_SUPERADMIN.md).

---

## 📁 Project Structure

```
c3techie-fastapi-kit/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI pipeline
│       └── cd.yml                    # Deployment workflow
├── .gitignore                        # Git ignore file
├── .env.example                      # Example environment variables
├── .flake8                           # Flake8 configuration
├── docker-compose.yml                # Docker Compose for local development
├── Dockerfile                        # Docker image definition
├── alembic.ini                       # Alembic configuration
├── pyproject.toml                    # Poetry project definition
├── README.md                         # Project documentation
├── run.py                            # Application entry point
├── src/
│   └── app/
│       ├── __init__.py               # Package marker
│       ├── main.py                   # FastAPI application initialization
│       ├── config.py                 # Global configuration settings
│       ├── dependencies.py           # Global dependency injection
│       ├── api/
│       │   ├── __init__.py           # API package marker
│       │   ├── routes/
│       │   │   ├── __init__.py       # Routes package marker
│       │   │   ├── health.py         # Health check endpoints
│       │   │   └── v1/               # API version 1
│       │   │       ├── __init__.py   # V1 package marker
│       │   │       ├── router.py     # Main V1 router
│       │   │       ├── auth.py       # Auth endpoints
│       │   │       ├── users.py      # User management endpoints
│       │   │       ├── admins.py     # Admin management endpoints
│       │   └── deps.py               # API-specific dependencies
│       ├── core/
│       │   ├── __init__.py           # Core package marker
│       │   ├── security.py           # Security utilities (JWT, password hashing)
│       │   ├── exceptions.py         # Custom exceptions
│       │   ├── middleware.py         # Custom middleware
│       │   └── permissions.py        # Role-based permissions
│       │   ├── rate_limiter.py       # Request rate limiting
│       │   ├── sanitizer.py          # Input sanitization
│       │   ├── password_policy.py    # Password strength rules
│       ├── db/
│       │   ├── __init__.py           # DB package marker
│       │   ├── session.py            # Database session management
│       │   ├── base.py               # Base model with common fields
│       │   └── migrations/           # Alembic migrations directory
│       │       └── versions/         # Migration versions
│       ├── domains/
│       │   ├── __init__.py           # Domains package marker
│       │   ├── shared/               # Shared domain components
│       │   │   ├── __init__.py
│       │   │   ├── models/           # Shared models (User, Admin, etc.)
│       │   │   │   ├── __init__.py
│       │   │   │   ├── user.py       # User model
│       │   │   │   ├── admin.py      # Admin model
│       │   │   │   ├── audit_log.py  # Audit model
│       │   │   │   └── base.py       # Base domain model
│       │   │   │   └── password_reset.py       # Reset Password
│       │   │   ├── schemas/          # Shared schemas
│       │   │   │   ├── __init__.py
│       │   │   │   ├── user.py       # User schemas
│       │   │   │   ├── admin.py      # Admin schemas
│       │   │   │   ├── audit_log.py  # Audit schemas
│       │   │   │   └── base.py       # Base schema
│       │   │   ├── crud/             # Shared CRUD operations
│       │   │   │   ├── __init__.py
│       │   │   │   ├── user.py       # User CRUD
│       │   │   │   ├── admin.py      # Admin CRUD
│       │   │   │   └── base.py       # Base CRUD
│       │   │   └── services/         # Shared services
│       │   │       ├── __init__.py
│       │   │       ├── auth_service.py       # Authentication service
│       │   │       └── user_service.py       # User management service
│       │   │       └── admin_service.py      # Admin management service
│       └── utils/
│           ├── __init__.py           # Utils package marker
│           ├── logging.py            # Logging utilities
│           ├── email.py              # Email utilities
│           ├── date.py               # Date/time utilities
│           └── validators.py         # Custom validators
│           └── cache.py              # Redis caching layer
```

---

## 🔧 Other Resources

- ✍️ [CONTRIBUTING.md](./CONTRIBUTING.md) — How to contribute to this project
- 🐳 Docker support included (see `docker-compose.yml`)
- ✅ GitHub Actions CI/CD (in `.github/workflows/`)
- 🧪 Run tests: `poetry run pytest`

---

## ✅ You're Ready!

Happy building! If you run into issues, feel free to open a discussion or bug report via GitHub Issues.

---

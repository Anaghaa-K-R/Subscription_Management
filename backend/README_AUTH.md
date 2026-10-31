# SubscriptIQ — Authentication & Account Management (Module 1)

## Overview
Module 1 implements complete, production-ready user authentication and account management for **SubscriptIQ**. It is integrated with PostgreSQL hosted on Supabase using SQLAlchemy, enforces password hashing via **Argon2id**, generates secure **JWT** access tokens for session management, and manages password recovery through **single-use, expiring SHA-256 hashed tokens**.

---

## Architecture & Security Features

1. **Password Security**:
   - Argon2id password hashing via `argon2-cffi`. Plaintext passwords are never stored or logged.
   - Strict password complexity enforcement (>8 characters, >=1 uppercase letter, >=1 lowercase letter, >=1 special character).
2. **Account Protection**:
   - Case-insensitive email normalization and database-level unique constraint handling.
   - Friendly and secure duplicate account prevention.
3. **Session Management**:
   - Cryptographically signed JWT tokens issued via `PyJWT`.
   - Authenticated endpoint `/auth/me` with Bearer token authentication dependency (`get_current_user`).
   - Profile responses never expose password hashes or sensitive internal tokens.
4. **Forgot & Reset Password Flow**:
   - Uniform response timing and messaging to eliminate email enumeration attacks.
   - Cryptographically random raw tokens (`secrets.token_urlsafe(32)`) delivered via background email tasks.
   - Only the **SHA-256 hash** of the reset token is stored in the database.
   - Single-use and expiration enforcement (default 15 minutes).
5. **CORS Configuration**:
   - Configured in [backend/main.py](main.py) for local frontend integration (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`).
6. **Dual-Environment Path Compatibility**:
   - Works seamlessly when imported from either project root or the `backend/` directory.

---

## API Endpoints

### 1. Register User
- **Method & Path**: `POST /auth/register`
- **Status Code**: `201 Created`
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "StrongPassword!2026"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane@example.com",
    "is_active": true,
    "created_at": "2026-10-31T15:00:00Z"
  }
  ```

### 2. Login User
- **Method & Path**: `POST /auth/login`
- **Status Code**: `200 OK`
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "password": "StrongPassword!2026"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

### 3. Get Current User Profile
- **Method & Path**: `GET /auth/me`
- **Status Code**: `200 OK`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**:
  ```json
  {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane@example.com",
    "is_active": true,
    "created_at": "2026-10-31T15:00:00Z"
  }
  ```

### 4. Request Password Reset
- **Method & Path**: `POST /auth/forgot-password`
- **Status Code**: `200 OK`
- **Request Body**:
  ```json
  {
    "email": "jane@example.com"
  }
  ```
- **Response**:
  ```json
  {
    "message": "If this email is registered in our system, you will receive a password reset link shortly."
  }
  ```

### 5. Reset Password
- **Method & Path**: `POST /auth/reset-password`
- **Status Code**: `200 OK`
- **Request Body**:
  ```json
  {
    "token": "<raw_token_from_email_link>",
    "new_password": "NewStrongPassword!2026"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Password has been successfully updated."
  }
  ```

---

## Environment Variable Configuration (`.env`)

Configure the following variables in `backend/.env` or the root `.env`:

```env
# Database Connection (Supabase PostgreSQL)
DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@<HOST>:5432/postgres

# JWT Token Settings
JWT_SECRET_KEY=your_secure_random_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
RESET_TOKEN_EXPIRE_MINUTES=15

# Frontend Base URL
FRONTEND_URL=http://localhost:5173

# Email / SMTP Settings (Optional - fallback to safe logging notice if omitted)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAILS_FROM_EMAIL=noreply@subscriptiq.com
```

---

## How to Start FastAPI

From the repository root using the existing `.venv`:

```powershell
.\.venv\Scripts\uvicorn.exe backend.main:app --reload --port 8000
```

Or from inside the `backend/` directory:

```powershell
cd backend
..\.venv\Scripts\uvicorn.exe main:app --reload --port 8000
```

- **API Base**: `http://localhost:8000/`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc UI**: `http://localhost:8000/redoc`

---

## Automated Testing Instructions

Run the 18 comprehensive authentication tests:

```powershell
.\.venv\Scripts\pytest.exe backend\tests\test_auth.py
```

Run the entire backend test suite (including Member 3 Billing, Finance, and Model tests):

```powershell
.\.venv\Scripts\pytest.exe backend\tests
```

# SubscriptIQ — Authentication & Account Management (Module 1)

## Overview
Module 1 implements secure user authentication and account management for SubscriptIQ. It integrates with PostgreSQL hosted on Supabase using SQLAlchemy and Alembic, hashes passwords using Argon2, manages sessions using JWT Bearer tokens, and handles password recovery with single-use, hashed expiring tokens.

---

## Architecture & Security Features

1. **Password Security**:
   - Argon2id password hashing via `argon2-cffi`. Never logs or stores plaintext passwords.
   - Enforces complexity rules: >8 characters, contains at least one uppercase letter, one lowercase letter, and one special character.
2. **Account Protection**:
   - Unique, indexed email validation via Pydantic `EmailStr`.
   - Prevents duplicate accounts with case-insensitive matching.
3. **Session Management**:
   - Issues cryptographically signed JWT tokens (`PyJWT`).
   - Authenticated endpoint `/auth/me` with Bearer token authentication dependency (`get_current_user`).
4. **Forgot & Reset Password Flow**:
   - Uniform response timing and messaging to eliminate email enumeration attacks.
   - Cryptographically random raw tokens (`secrets.token_urlsafe(32)`) delivered via background email tasks.
   - Only the **SHA-256 hash** of the reset token is stored in the database.
   - Single-use and expiration enforcement (default 15 minutes).
5. **CORS Configuration**:
   - Configured in [backend/main.py](main.py) for local frontend integration (`http://localhost:5173`, `http://127.0.0.1:5173`).
6. **Robust Environment Loading**:
   - [backend/config.py](config.py) and [backend/database.py](database.py) resolve `.env` whether invoked from the project root or from `backend/`.

---

## API Endpoints

### 1. Register
- **URL**: `POST /auth/register`
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "StrongPassword!2026"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "e63d3fb6-7ce2-4753-91ee-01f654b036ca",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "is_active": true,
    "created_at": "2026-10-31T14:00:00Z"
  }
  ```

### 2. Login
- **URL**: `POST /auth/login`
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "password": "StrongPassword!2026"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "<jwt-token-string>",
    "token_type": "bearer"
  }
  ```

### 3. Get Current User Profile
- **URL**: `GET /auth/me`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response (200 OK)**:
  ```json
  {
    "id": "e63d3fb6-7ce2-4753-91ee-01f654b036ca",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "is_active": true,
    "created_at": "2026-10-31T14:00:00Z"
  }
  ```

### 4. Forgot Password
- **URL**: `POST /auth/forgot-password`
- **Request Body**:
  ```json
  {
    "email": "jane@example.com"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "message": "If this email is registered in our system, you will receive a password reset link shortly."
  }
  ```

### 5. Reset Password
- **URL**: `POST /auth/reset-password`
- **Request Body**:
  ```json
  {
    "token": "<raw_token_from_email>",
    "new_password": "NewStrongPassword!2026"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "message": "Password has been successfully updated."
  }
  ```

---

## Environment Variables (`.env`)

Configure the following variables in `backend/.env` or root `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@<HOST>:5432/postgres
JWT_SECRET_KEY=your_secure_random_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
RESET_TOKEN_EXPIRE_MINUTES=15
FRONTEND_URL=http://localhost:5173

# Email / SMTP Settings (Optional, logs safe notice if omitted)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAILS_FROM_EMAIL=noreply@subscriptiq.com
```

---

## Running Migrations

To apply database migrations to Supabase via Alembic:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

---

## Running the Backend

From the repository root or `backend/` directory:

```powershell
# From backend directory
cd backend
..\.venv\Scripts\uvicorn.exe main:app --reload --port 8000

# Or from project root
.\.venv\Scripts\uvicorn.exe backend.main:app --reload --port 8000
```

Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Running Tests

Execute all tests (Module 1 Auth + Member 3 Billing/Finance services):

```powershell
.\.venv\Scripts\pytest.exe backend\tests
```

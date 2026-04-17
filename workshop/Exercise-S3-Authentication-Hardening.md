# Exercise S3: Authentication Hardening
## TaskForce Pro Security Workshop

**Objective:** Build an Auth Hardening agent and use it to fix JWT secrets, password hashing, credential logging, and rate limiting

**Time:** 60 minutes | **Difficulty:** Intermediate | **Module:** 3 of 5

---

## 🎯 What You'll Fix

| ID | Vulnerability | File | Risk |
|----|--------------|------|------|
| SEC-003 | JWT secret hardcoded; tokens never expire | `app/auth/jwt_handler.py` | Critical |
| SEC-005 | Admin password `admin123` hardcoded | `app/auth/admin_setup.py` | High |
| SEC-011 | Passwords logged in plaintext | `app/api/auth_api.py` | High |
| SEC-012 | No rate limiting on login | `app/api/auth_api.py` | High |
| SEC-013 | Passwords stored and compared in plaintext | `app/core/database.py`, `app/api/auth_api.py` | Critical |

---

## 🤖 Step 1: Open the Auth Hardening Agent

A `auth-hardening-agent.agent.md` agent file has been pre-created at:

```
.github/copilot-agents/auth-hardening-agent.agent.md
```
create it under `.github/agents` directory.
**To activate it:**
1. Open **GitHub Copilot Chat** (Ctrl+Alt+I)
2. Click the agent picker and select **Auth Hardening Agent**
3. You are now in agent mode

---

## 🔍 Phase 1: Understand the Auth Weaknesses

### Step 2: Get a Full Auth Review

```
Review the entire authentication system.
Check app/auth/jwt_handler.py, app/auth/admin_setup.py,
app/api/auth_api.py, and app/core/database.py.

For each file, list every security weakness:
hardcoded secrets, weak JWT config, plaintext passwords,
credential logging, missing rate limiting.
```

<details>
<summary>✅ Expected findings</summary>

**`jwt_handler.py`:**
- `SECRET_KEY = "super-secret-jwt-key-do-not-share-2026"` — hardcoded, anyone with repo access can forge tokens
- `options={"verify_exp": False}` — tokens are valid forever

**`admin_setup.py`:**
- `ADMIN_PASSWORD = "admin123"` — trivially guessable, hardcoded in source
- `ADMIN_API_KEY = "sk_admin_..."` — hardcoded API key

**`auth_api.py`:**
- `logger.debug(f"password: {password}")` — plaintext password in logs
- `"password": password` in JWT payload — password travels to every service
- No login rate limiting

**`database.py` seed:**
- All user passwords stored as plaintext strings (`"Password123"`, `"admin123"`)

</details>

---

### Step 3: Demonstrate JWT Forgery

With the app running, run this Python snippet to forge an admin token without knowing the password:

```python
import jwt

forged = jwt.encode(
    {"user_id": 1, "email": "admin@globaltech.com", "role": "admin"},
    "super-secret-jwt-key-do-not-share-2026",   # hardcoded secret from jwt_handler.py
    algorithm="HS256"
)
print(forged)
```

Use that token to call any authenticated endpoint — it works because the secret is public.

```
I forged a valid admin JWT token using the hardcoded secret visible in jwt_handler.py.
What OWASP category covers this? What is the complete attack path an external attacker
would use if this file was pushed to a public repository?
```

---

## 🔧 Phase 2: Fix JWT Configuration

### Step 4: Externalise the JWT Secret

Open `app/auth/jwt_handler.py` and select the `JWTHandler` class definition.

```
Fix the JWTHandler class:
- Load SECRET_KEY from os.getenv("JWT_SECRET_KEY")
- Raise ValueError at class-load time if the env var is missing or shorter than 32 characters
- Set ACCESS_TOKEN_EXPIRE_MINUTES to 30
- Remove all hardcoded API_KEYS, ENCRYPTION_KEY, and PASSWORD_SALT constants
```

---

### Step 5: Enforce Token Expiry

Select the `decode_token` method in `jwt_handler.py`.

```
Fix decode_token to enforce token expiration:
- Remove options={"verify_exp": False}
- Catch ExpiredSignatureError specifically and return None
- Catch InvalidTokenError for all other JWT failures
- Log a warning (not the token value) when a token is rejected
```

<details>
<summary>✅ Correct decode_token pattern</summary>

```python
@classmethod
def decode_token(cls, token: str):
    try:
        return jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Rejected expired JWT token")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Rejected invalid JWT: {type(e).__name__}")
        return None
```

</details>

---

## 🔧 Phase 3: Fix Password Storage

### Step 6: Add bcrypt Hashing

```
Fix the register() and login() functions in app/api/auth_api.py:

1. In register(): hash the password with passlib bcrypt before INSERT
2. In login(): fetch by email only, then verify with bcrypt.verify()
3. Remove "password" from the JWT payload entirely
4. Remove the debug log line that prints the password

Show me the complete updated code for both functions.
```

<details>
<summary>✅ Core pattern</summary>

```python
from passlib.hash import bcrypt

# register — hash before storing
hashed = bcrypt.hash(password)
cur.execute("INSERT INTO users (email, password, ...) VALUES (?,?,...)", (email, hashed, ...))

# login — verify after fetching
cur.execute("SELECT id, email, password, role FROM users WHERE email = ?", (email,))
user = cur.fetchone()
if not user or not bcrypt.verify(password, user["password"]):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

</details>

---

### Step 7: Add Password Strength Validation

```
Add a validate_password_strength() function to app/api/auth_api.py.

Policy: minimum 12 characters, at least 1 uppercase, 1 lowercase, 1 digit, 1 special character.
Raise HTTPException(400) with a message listing what is missing.
Call it from register() before hashing.
```

---

## 🔧 Phase 4: Fix Admin Credentials

### Step 8: Externalise Admin Password

Open `app/auth/admin_setup.py` and select the constants block at the top.

```
Fix admin_setup.py:
- Load ADMIN_EMAIL from os.getenv("ADMIN_EMAIL")
- Load ADMIN_PASSWORD from os.getenv("ADMIN_PASSWORD")
- Raise ValueError at startup if either is missing
- Remove ADMIN_API_KEY, DEV_ADMIN_CREDS, STAGING_ADMIN_CREDS, PROD_ADMIN_CREDS, SERVICE_ACCOUNTS
- Hash the password with bcrypt before storing
- Remove all logger lines that print email or password values
```

---

## 🔧 Phase 5: Add Rate Limiting

### Step 9: Implement Login Rate Limiting

```
Add in-memory rate limiting to the login() function in app/api/auth_api.py:
- Track failed attempts per email address
- Allow maximum 5 failed attempts within 5 minutes
- Return HTTP 429 when the limit is exceeded
- Reset the counter on successful login
Show me the implementation.
```

---

## ✅ Phase 6: Verify

### Step 10: Run the Tests

```bash
pytest tests/test_security_vulnerabilities.py::TestJWTSecurity -v
pytest tests/test_security_vulnerabilities.py::TestCredentials -v
```

Expected: **5 PASS, 0 FAIL**

### Step 11: Confirm JWT Forgery No Longer Works

```
JWT_SECRET_KEY=a-fresh-32-char-secret-for-testing python -c "
import jwt
try:
    jwt.decode('eyJhbGciOiJIUzI1NiJ9...', 'super-secret-jwt-key-do-not-share-2026', algorithms=['HS256'])
    print('VULNERABLE')
except Exception as e:
    print('Protected:', e)
"
```

After the fix: the hardcoded secret is wrong — decode raises `InvalidSignatureError`.

### Step 12: Ask the Agent for Final Verification

```
Review app/auth/jwt_handler.py, app/auth/admin_setup.py, and app/api/auth_api.py.
Confirm:
1. No hardcoded secrets remain
2. Token expiry is enforced
3. No credentials appear in any log statement
4. Rate limiting is present on the login endpoint
```

---

## 🏆 Success Criteria

- [ ] `pytest TestJWTSecurity` — all PASS
- [ ] `pytest TestCredentials` — all PASS
- [ ] `JWT_SECRET_KEY` loaded from environment, startup fails without it
- [ ] Forged token with old hardcoded secret is rejected
- [ ] bcrypt used for all password storage and comparison
- [ ] No passwords or tokens in any log output

---

## 📚 Key Takeaway

> Hardcoded JWT secrets are as dangerous as hardcoded passwords.  
> `verify_exp: False` makes tokens immortal — an attacker only needs to steal one, ever.

**Next:** [Exercise S4 — Fix Authorization & IDOR](Exercise-S4-Authorization-IDOR.md)

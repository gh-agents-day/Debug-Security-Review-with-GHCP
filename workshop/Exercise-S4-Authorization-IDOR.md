# Exercise S4: Fix Authorization & IDOR
## TaskForce Pro Security Workshop

**Objective:** Build an Access Control agent and use it to find and fix Insecure Direct Object References and broken authorization in TaskForce Pro

**Time:** 60 minutes | **Difficulty:** Intermediate–Advanced | **Module:** 4 of 5

---

## 🎯 What You'll Fix

**IDOR** (Insecure Direct Object Reference) means any logged-in user can access any resource by guessing its numeric ID — the app never checks ownership. Task #4 contains a **$2.5M Bank of America invoice** and task #7 contains an **$8M acquisition deal**. The attacker account (`attacker@evil.com`) can currently read, modify, or delete them.

| ID | Vulnerability | File | Risk |
|----|--------------|------|------|
| SEC-004 | IDOR — no ownership check on tasks | `app/api/task_api.py` | Critical |
| SEC-004 | IDOR — any user can view any user profile | `app/api/auth_api.py` | High |
| SEC-004 | IDOR — any user can delete any attachment | `app/api/attachment_api.py` | High |
| SEC-020 | No audit log for sensitive data access | `app/api/task_api.py` | Medium |
| SEC-014 | CORS allows all origins (`*`) | `main.py` | Medium |

---

## 🤖 Step 1: Open the Access Control Agent

A `access-control-agent.agent.md` agent file has been pre-created at:

```
.github/copilot-agents/access-control-agent.agent.md
```
create it under `.github/agents` directory.

**To activate it:**
1. Open **GitHub Copilot Chat** (Ctrl+Alt+I)
2. Click the agent picker and select **Access Control Agent**
3. You are now in agent mode

---

## 🔍 Phase 1: Demonstrate the IDOR Attack

### Step 2: Read Confidential Data Without Permission

First, log in as the attacker to get a token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login?email=attacker%40evil.com&password=hacked"
```

Copy the `access_token` from the response. Now read confidential task #4:

```bash
# Replace <ATTACKER_TOKEN> with the token from above
curl "http://localhost:8000/api/v1/tasks/4?current_user_id=6" \
  -H "Authorization: Bearer <ATTACKER_TOKEN>"
```

The response reveals: `"CONFIDENTIAL: Invoice #INV-2026-0412, amount $2,500,000"` — the attacker can read data that belongs to someone else.

```
Looking at task_api.py, explain exactly which line causes this IDOR vulnerability.
Why is accepting current_user_id as a query parameter also insecure?
What is the complete attack scenario? 
What is the OWASP classification?
```

---

### Step 3: Map All IDOR Points

```
Find every endpoint in task_api.py, auth_api.py, project_api.py, and attachment_api.py
that accepts a numeric resource ID but does NOT verify the caller owns or has access to it.
List each endpoint, the missing check, and the worst-case data exposure.
```

---

## 🔧 Phase 2: Fix IDOR in Task Endpoints

### Step 4: Create the Auth Dependency

The root cause is that identity comes from an untrusted query parameter. We need a FastAPI dependency that extracts user identity from a validated JWT instead.

```
Create a FastAPI dependency function called get_current_user_id in app/api/task_api.py.
It should:
1. Read the Authorization header (Bearer token)
2. Validate it using JWTHandler.decode_token()
3. Return the integer user_id from the payload
4. Raise HTTPException(401) if the header is missing or the token is invalid
```

<details>
<summary>✅ Expected dependency</summary>

```python
from fastapi import Header, Depends
from typing import Optional

def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    from app.auth.jwt_handler import JWTHandler
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[len("Bearer "):]
    payload = JWTHandler.decode_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["user_id"])
```

</details>

---

### Step 5: Add Ownership Check to get_task

Open `app/api/task_api.py` and select the `get_task` function.

```
Fix get_task to enforce proper authorization:
1. Replace the current_user_id query param with the get_current_user_id dependency
2. After fetching the task, check:
   - task.created_by == current_user_id → allow
   - task.assigned_to == current_user_id → allow
   - caller's role is "admin" → allow
   - Otherwise → raise HTTPException(403, "Access denied")
3. Fetch the caller's role with a parameterised query
```

<details>
<summary>✅ Ownership check pattern</summary>

```python
@router.get("/{task_id}")
async def get_task(
    task_id: int,
    current_user_id: int = Depends(get_current_user_id),
):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id = ?", (current_user_id,))
    caller = cur.fetchone()
    role = caller["role"] if caller else "member"

    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cur.fetchone()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    is_owner    = task["created_by"] == current_user_id
    is_assignee = task["assigned_to"] == current_user_id
    is_admin    = role == "admin"

    if not (is_owner or is_assignee or is_admin):
        raise HTTPException(status_code=403, detail="Access denied")

    return dict(task)
```

</details>

---

### Step 6: Fix update_task and delete_task

```
Apply the same ownership check pattern to update_task() and delete_task() in task_api.py.

For delete_task, also insert an audit log entry before deleting:
  INSERT INTO audit_log (user_id, action, resource, detail) VALUES (?,?,?,?)
  where action="DELETE" and resource="tasks/{task_id}"
```

---

## 🔧 Phase 3: Fix IDOR in User Profile

### Step 7: Fix get_user_profile

Select `get_user_profile` in `app/api/auth_api.py`.

```
Fix get_user_profile:
- Require a valid Bearer token (use get_current_user_id dependency)
- A user can only view their own profile unless their role is "admin"
- Return 403 for unauthorized attempts
- Remove the password field from the response
```

---

### Step 8: Fix list_all_users

```
The GET /api/v1/auth/users endpoint returns all users including passwords with no auth.

Fix it to:
1. Require a valid Bearer token
2. Require admin role — return 403 if not admin
3. Exclude the password field from every record in the response
```

---

## 🔧 Phase 4: Fix CORS

### Step 9: Restrict CORS Origins

Open `main.py` and select the `CORSMiddleware` block.

```
Fix CORS to stop allowing all origins:
- Load allowed origins from os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
- Split on comma to support multiple origins
- Never use allow_origins=["*"] with allow_credentials=True
- Add a comment explaining why wildcard CORS is dangerous
```

<details>
<summary>✅ Expected fix</summary>

```python
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins only — never *
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

</details>

---

## 🔧 Phase 5: Add Audit Logging

### Step 10: Log Sensitive Operations

```
Add audit log entries for the following task operations in task_api.py.
Write to the audit_log table with user_id, action, resource, and detail.

Operations to audit:
- get_task: action="READ", after successful access
- update_task: action="UPDATE", before applying changes
- delete_task: action="DELETE", before deleting
- create_task: action="CREATE", after successful insert
```

---

## ✅ Phase 6: Verify

### Step 11: Run the Tests

```bash
pytest tests/test_security_vulnerabilities.py::TestAuthorization -v
```

Expected: **3 PASS, 0 FAIL**

### Step 12: Confirm the Attack No Longer Works

```bash
# Attacker token — should now get 403 on task #4
curl "http://localhost:8000/api/v1/tasks/4" \
  -H "Authorization: Bearer <ATTACKER_TOKEN>"
```

Expected response: `{"detail": "Access denied"}` with HTTP 403.

### Step 13: Ask the Agent for Final Verification

```
Review task_api.py, auth_api.py, and attachment_api.py.
Confirm that every endpoint that accepts a resource ID now verifies the caller owns it.
Are there any remaining IDOR points?
```

---

## 🏆 Success Criteria

- [ ] `pytest TestAuthorization` — 3 PASS
- [ ] Attacker token returns 403 on task #4
- [ ] `current_user_id` no longer accepted as a query parameter for identity
- [ ] User list endpoint requires admin role
- [ ] CORS no longer uses `allow_origins=["*"]`
- [ ] Audit log entries written for task reads, creates, updates, and deletes

---

## 📚 Key Takeaway

> Never trust a user-supplied identity claim. Always extract `user_id` from a server-signed JWT.  
> Ownership checks are not optional — every resource endpoint must verify the caller has rights.

**Next:** [Exercise S5 — Complete Security Audit](Exercise-S5-Complete-Security-Audit.md)

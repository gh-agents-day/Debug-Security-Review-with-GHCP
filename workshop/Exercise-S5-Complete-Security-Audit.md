# Exercise S5: Complete Security Audit
## TaskForce Pro Security Workshop

**Objective:** Use your complete agent toolkit to find and fix all remaining vulnerabilities and achieve a zero-finding security audit

**Time:** 90 minutes | **Difficulty:** Advanced | **Module:** 5 of 5

---

## 🎯 What You'll Complete

After Exercises S1–S4, the major vulnerabilities are fixed. Several remain:

| ID | Category | File | Fix |
|----|---------|------|-----|
| SEC-008 | Debug mode in production | `main.py` | Environment-gated flag |
| SEC-009 | XSS — unsanitised HTML output | `task_api.py`, `auth_api.py` | `html.escape()` |
| SEC-016 | Path traversal in file upload | `attachment_api.py` | Sanitise filename |
| SEC-019 | Stack trace in error responses | `main.py` | Remove traceback from response |
| BUG-002 | Database connections not closed | Multiple files | Context managers |
| BUG-003 | Exceptions swallowed silently | Multiple files | `logger.error(..., exc_info=True)` |
| BUG-004 | N+1 queries | `project_api.py` | Single JOIN query |

**Goal:**

## 🤖 Step 1: Activate the Security Audit Agent

The comprehensive `security-audit-agent.agent.md` was pre-created at:

```
.github/copilot-agents/security-audit-agent.agent.md
```
create it under `.github/agents` directory.

You also have the four specialised agents from earlier exercises.

**To activate the Security Audit Agent:**
1. Open **GitHub Copilot Chat** (Ctrl+Alt+I)
2. Click the agent picker and select **TaskForce Pro — Security Audit Agent**
3. You are now in agent mode

---

## 🔍 Phase 1: Run Automated Scanning Tools

### Step 2: Bandit Static Analysis

```bash
pip install bandit
bandit -r app/ -f txt -o bandit-report.txt
cat bandit-report.txt
```

Once the report is generated, ask the agent:

```
I ran Bandit on the codebase and got this output:
[paste the contents of bandit-report.txt here]

Prioritise the findings by severity.
Map each Bandit issue ID to the SEC- or BUG- codes from the README.
Which findings were already fixed in S1–S4, and which are new?
```

---

### Step 3: detect-secrets Scan

```bash
pip install detect-secrets
detect-secrets scan --all-files > secrets-baseline.json
python -c "import json; d=json.load(open('secrets-baseline.json')); print(sum(len(v) for v in d['results'].values()), 'secrets found')"
```

Ask the agent:

```
detect-secrets found [N] results.
Review secrets-baseline.json and tell me which are real secrets
versus false positives (test fixtures, example values).
What still needs to be externalised?
```

---

### Step 4: Dependency Vulnerability Scan

```bash
pip install pip-audit
pip-audit -r requirements.txt
```

Ask the agent:

```
pip-audit found these vulnerable packages:
[paste output here]

For each finding, recommend the safe version to upgrade to
and whether upgrading is a breaking change for this app.
```

---

## 🔧 Phase 2: Fix Information Leakage

### Step 5: Fix Debug Mode Exposure

Open `main.py`. The server starts with `debug=True` and the root endpoint returns internal system info.

```
Fix the debug mode exposure in main.py:
1. DEBUG should only be True when ENVIRONMENT env var is "development"
2. Remove the "debug" and "database" fields from the root endpoint response
3. Show me the complete fixed root endpoint and the fixed app startup
```

<details>
<summary>✅ Expected fix</summary>

```python
import os

DEBUG = os.getenv("ENVIRONMENT", "development") == "development"

@app.get("/")
async def root():
    return {
        "application": "TaskForce Pro",
        "version": "2.4.1",
        "status": "running",
        # Removed: debug, database, environment fields
    }
```

</details>

---

### Step 6: Remove Stack Traces from Error Responses

Select the `global_exception_handler` in `main.py`.

```
Fix the global exception handler:
- Log the full exception with exc_info=True for server-side debugging
- Return only {"error": "Internal server error"} — no traceback, no exception type, no file paths
- Keep the 500 status code
```

<details>
<summary>✅ Expected fix</summary>

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
```

</details>

---

## 🔧 Phase 3: Fix XSS Vulnerabilities

### Step 7: Escape HTML in Task Responses

```
In app/api/task_api.py, user-supplied text fields (title, description, comments)
are returned directly in JSON. If a browser renders them as HTML, a stored
XSS attack is possible.

Add html.escape() to all string fields in the task response dictionaries:
title, description, and comment.
Show me the exact changes for search_tasks(), get_task(), and get_task_comments().
```

<details>
<summary>✅ Pattern to apply</summary>

```python
import html

# In every response dict — wrap user-supplied string fields:
"title":       html.escape(row["title"] or ""),
"description": html.escape(row["description"] or ""),
"comment":     html.escape(row["comment"] or ""),
```

</details>

---

## 🔧 Phase 4: Fix Path Traversal

### Step 8: Sanitise File Upload Filenames

Open `app/api/attachment_api.py`.

```
The upload_attachment function is vulnerable to path traversal:
  file_path = os.path.join(UPLOAD_DIR, filename)

If filename is "../../etc/passwd" it writes outside the intended directory.

Fix it to:
1. Strip directory components with os.path.basename()
2. Only allow safe extensions: .pdf .docx .xlsx .png .jpg .txt
3. Verify the resolved path starts with UPLOAD_DIR
4. Raise HTTP 400 for any unsafe filename or disallowed extension
Show the complete fixed function.
```

<details>
<summary>✅ Expected fix</summary>

```python
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".png", ".jpg", ".txt"}

safe_name = os.path.basename(filename)
_, ext = os.path.splitext(safe_name)
if ext.lower() not in ALLOWED_EXTENSIONS:
    raise HTTPException(400, f"File type not allowed: {ext}")

file_path = os.path.realpath(os.path.join(UPLOAD_DIR, safe_name))
if not file_path.startswith(os.path.realpath(UPLOAD_DIR)):
    raise HTTPException(400, "Invalid filename")
```

</details>

---

## 🔧 Phase 5: Fix Code Quality Issues

### Step 9: Fix Exception Swallowing

```
Find every bare except block or except Exception block in the app directory
that does not call logger.error(..., exc_info=True).
For each one, add the missing log call so the full stack trace reaches the logs.
```

---

### Step 10: Fix Database Connections Not Closed

```
Find every place in the app directory where get_db_connection() is called
but the connection is never explicitly closed.
Fix each one to use a try/finally block that calls conn.close().
```

---

### Step 11: Fix N+1 Query in Projects

Open `app/api/project_api.py` and select the `list_projects` function.

```
Fix the N+1 query problem — the function currently runs one SQL query per
project to fetch the owner. Replace it with a single JOIN query:

SELECT p.id, p.name, p.description, p.status, u.first_name, u.last_name
FROM projects p
LEFT JOIN users u ON u.id = p.owner_id

Show me the complete fixed function.
```

---

## ✅ Phase 6: Final Verification

### Step 12: Run the Full Test Suite

```bash
pytest tests/test_security_vulnerabilities.py -v
```

Expected: **ALL PASS — zero failures**

### Step 13: Re-run Bandit

```bash
bandit -r app/ -f txt
```

Expected: no HIGH or CRITICAL findings.

### Step 14: Ask the Agent for a Final Security Report

```
Perform a final OWASP Top 10 review of the entire codebase.
For each OWASP category, tell me:
1. Whether the codebase is now protected
2. Which specific fix in S1–S5 addressed it
3. Any residual risk that is still present

Give me a sign-off verdict: PASS or FAIL with justification.
```

---

## 🏆 Final Success Criteria

- [ ] `pytest tests/test_security_vulnerabilities.py` — all PASS
- [ ] Bandit reports no HIGH or CRITICAL findings
- [ ] Stack traces do not appear in HTTP error responses
- [ ] Debug info absent from root endpoint response
- [ ] File upload rejects `../../etc/passwd` with HTTP 400
- [ ] XSS payload `<script>alert(1)</script>` is escaped in task responses
- [ ] All exception handlers log with `exc_info=True`
- [ ] Security Audit Agent gives PASS verdict

---

## 🎓 Workshop Complete

You have built and used **5 custom Copilot agents** to:

| Agent | Exercises | Vulnerabilities Fixed |
|-------|-----------|-----------------------|
| `secret-scanner-agent` | S1 | AWS keys, DB passwords, JWT secrets, API keys |
| `sql-injection-agent` | S2 | 5 SQL injection points across task + auth APIs |
| `auth-hardening-agent` | S3 | JWT forgery, plaintext passwords, credential logging, brute force |
| `access-control-agent` | S4 | IDOR on tasks, profiles, attachments; wildcard CORS |
| `security-audit-agent` | S5 | Debug exposure, XSS, path traversal, N+1, swallowed exceptions |

Each agent lives in `.github/copilot-agents/` and can be reused on any project.

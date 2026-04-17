# Exercise S2: Fix SQL Injection
## TaskForce Pro Security Workshop

**Objective:** Build a SQL Injection agent and use it to find, demonstrate, and fix every injection point in TaskForce Pro

**Time:** 60 minutes | **Difficulty:** Intermediate | **Module:** 2 of 5

---

## 🎯 Learning Objectives

1. Create a custom Copilot agent specialised in SQL injection detection
2. Identify every f-string and concatenated SQL pattern in the codebase
3. Demonstrate a real injection attack against the running application
4. Fix every vulnerable query using parameterised statements

**Tests to pass:**
```bash
pytest tests/test_security_vulnerabilities.py::TestSQLInjection -v
```
Expected before fix: **3 FAIL, 1 PASS** → Expected after fix: **4 PASS**

---

## 🤖 Step 1: Open the SQL Injection Agent

A `sql-injection-agent.agent.md` agent file has been pre-created at:

```
.github/copilot-agents/sql-injection-agent.agent.md
```
create it under `.github/agents` directory.

**To activate it:**
1. Open **GitHub Copilot Chat** (Ctrl+Alt+I)
2. Click the agent picker and select **SQL Injection Agent**
3. You are now in agent mode

---

## 🔍 Phase 1: Find the Vulnerabilities

### Step 2: Scan for Injection Points

```
Find every SQL injection vulnerability in the codebase.
For each one, show:
- File and line number
- The exact vulnerable SQL string
- Which variable is attacker-controlled
- A concrete attack payload that would succeed
```

<details>
<summary>✅ Expected findings</summary>

| File | ~Line | Vulnerable code | Attacker payload |
|------|-------|----------------|-----------------|
| `app/api/task_api.py` | 30 | `f"...LIKE '%{query}%'"` | `' OR '1'='1` |
| `app/api/task_api.py` | 68 | `f"...WHERE id = {task_id}"` | `1 OR 1=1` |
| `app/api/task_api.py` | 120 | `f"...VALUES ('{title}'...)"` | `'), (1,'hacked` |
| `app/api/auth_api.py` | 42 | `f"...email = '{email}'"` | `admin@globaltech.com' --` |
| `app/api/auth_api.py` | 79 | INSERT with concatenated values | same |

</details>

---

### Step 3: Demonstrate the Attack

With the app running (`python main.py`), prove the vulnerability is real:

```bash
# Attack 1 — Authentication bypass (login without a valid password)
curl -X POST "http://localhost:8000/api/v1/auth/login?email=admin%40globaltech.com'+--&password=anything"

# Attack 2 — Data dump via search (returns ALL tasks)
curl "http://localhost:8000/api/v1/tasks/search?query='+OR+'1'%3D'1"
```

Then ask the agent:

```
I ran GET /api/v1/tasks/search?query=' OR '1'='1 and got back all 8 tasks
including the confidential $2.5M Bank of America invoice.

Explain step by step:
1. The exact SQL statement that runs on the server
2. Why it returns every row
3. What a real attacker would do next
```

---

## 🔧 Phase 2: Fix the Vulnerabilities

### Step 4: Fix the Search Endpoint

Open `app/api/task_api.py` and select the entire `search_tasks` function.

```
Fix the search_tasks function to use parameterised queries.
The LIKE wildcards must be built in Python and passed as a parameter —
never embedded in the SQL string.
The function signature must not change.
```

<details>
<summary>✅ Correct pattern</summary>

```python
like_param = f"%{query}%"
cur.execute(
    "SELECT id, title, description, assigned_to, status, priority "
    "FROM tasks WHERE title LIKE ? OR description LIKE ?",
    (like_param, like_param),
)
```

</details>

---

### Step 5: Fix the Login Endpoint

Select the `login` function in `app/api/auth_api.py`.

```
Fix the login function:
1. Query by email only using a parameterised query (no password in SQL)
2. Compare the password in Python after fetching the user row
3. Remove the debug log line that prints credentials
```

<details>
<summary>✅ Correct pattern</summary>

```python
logger.info("Login attempt received")  # No credentials in logs

cur.execute("SELECT id, email, password, role FROM users WHERE email = ?", (email,))
user = cur.fetchone()

if not user or user["password"] != password:
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

> Password hashing is added in Exercise S3.

</details>

---

### Step 6: Fix All CRUD Endpoints in task_api.py

```
Fix every remaining SQL injection in app/api/task_api.py.
For get_task, create_task, update_task, delete_task, and get_task_comments:
- Replace all f-string SQL with cursor.execute(sql, (params,))
- Show me the before and after for each function
```

Apply every fix the agent provides.

---

### Step 7: Fix the Register Endpoint

```
Apply the same parameterised query fix to the register function in app/api/auth_api.py.
```

---

## ✅ Phase 3: Verify

### Step 8: Run the Tests

```bash
pytest tests/test_security_vulnerabilities.py::TestSQLInjection -v
```

Expected: **4 PASS, 0 FAIL**

### Step 9: Confirm Attacks No Longer Work

```bash
# Should return 401 (not a token)
curl -X POST "http://localhost:8000/api/v1/auth/login?email=admin%40globaltech.com'+--&password=x"

# Should return count: 0 (not all 8 tasks)
curl "http://localhost:8000/api/v1/tasks/search?query='+OR+'1'%3D'1"
```

### Step 10: Ask the Agent for a Final Review

```
Review app/api/task_api.py and app/api/auth_api.py.
Check every cursor.execute() call — is every user input parameterised?
Are there any remaining f-strings inside SQL strings?
Give me a final security verdict.
```

---

## 🏆 Success Criteria

- [ ] `pytest TestSQLInjection` — 4 PASS
- [ ] Login with `admin' --` payload returns 401
- [ ] Search with `' OR '1'='1` returns 0 results
- [ ] No f-strings remain inside SQL string literals
- [ ] No credentials in log output

---

## 📚 Key Takeaway

> SQL injection is eliminated entirely by never concatenating user input into SQL.  
> Always use `cursor.execute(sql, (params,))` — the database driver handles escaping.

**Next:** [Exercise S3 — Authentication Hardening](Exercise-S3-Authentication-Hardening.md)

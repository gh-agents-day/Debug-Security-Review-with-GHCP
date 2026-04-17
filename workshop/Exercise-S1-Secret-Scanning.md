# Exercise S1: Secret Scanning & Remediation
## TaskForce Pro Security Workshop

**Objective:** Build a Secret Scanner agent and use it to find and remediate every hardcoded credential in the codebase

**Time:** 30 minutes | **Difficulty:** Beginner | **Module:** 1 of 5

---

## 🎯 Learning Objectives

1. Create a custom Copilot agent for automated secret scanning
2. Find every hardcoded credential (AWS keys, DB passwords, JWT secrets, API keys)
3. Replace secrets with environment variables
4. Generate a complete `.env.example` for the project

---

## 📋 Scenario

**Company:** GlobalTech Industries  
**Incident:** AWS credentials committed to a public GitHub repo  
**Impact:** $45,000 AWS bill, 15,000 customer records exposed, $2.5M GDPR fine  
**Root Cause:** `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` hardcoded in `app/integrations/s3_client.py`

---

## 🤖 Step 1: Open the Secret Scanner Agent

A `secret-scanner-agent.agent.md` agent file has been pre-created for this workshop at:

```
.github/copilot-agents/secret-scanner-agent.agent.md
```
create it under `.github/agents` directory.


**To activate it:**
1. Open **GitHub Copilot Chat** (Ctrl+Alt+I)
2. Click the agent picker (sparkle icon or dropdown) and select **Secret Scanner Agent**
3. You are now in agent mode — every message goes to the scanner

---

## 🔍 Phase 1: Discover Hardcoded Secrets

### Step 2: Scan for AWS Credentials

Type this in the Copilot Chat panel (agent already selected):

```
Scan the entire codebase for hardcoded AWS credentials.
Report every file, line number, exact code, and severity.
```

<details>
<summary>✅ Expected findings</summary>

**`app/integrations/s3_client.py`**
- `AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"` — Critical
- `AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI..."` — Critical
- Line 35: credentials logged in debug statement
- Line 101: `BACKUP_AWS_CREDENTIALS` dictionary with a second set of keys

</details>

---

### Step 3: Scan for Database Credentials

```
Scan for hardcoded database credentials — passwords, connection strings, Redis URLs.
```

<details>
<summary>✅ Expected findings</summary>

**`config/production.yaml`**
- `password: "Pr0d#DB!P@ssw0rd2026"` — Critical
- Database URL with embedded password
- `password: "Red1s#Pr0dP@ss2026"` — High
- Redis URL with embedded password

</details>

---

### Step 4: Scan for JWT Secrets and API Keys

```
Scan for hardcoded JWT secret keys, admin passwords, and third-party API keys.
List each with file path, line number, and a risk rating.
```

<details>
<summary>✅ Expected findings</summary>

- `app/auth/jwt_handler.py:23` — `SECRET_KEY = "super-secret-jwt-key-do-not-share-2026"` (Critical)
- `app/auth/admin_setup.py:13` — `ADMIN_PASSWORD = "admin123"` (High)
- `app/auth/admin_setup.py:14` — `ADMIN_API_KEY = "sk_admin_super_secret_key_2026"` (High)
- `config/production.yaml:35-52` — Twilio, Stripe, Slack, SendGrid keys (High)

</details>

---

## 🛠️ Phase 2: Understand the Risk

### Step 5: Analyse Impact

```
For each secret category found, explain:
1. What an attacker can do with it
2. The business impact
3. OWASP category (A02:2021 Cryptographic Failures or A07:2021 Identification and Auth Failures)
```

---

## 🔧 Phase 3: Apply the Fixes

### Step 6: Fix AWS Credentials in s3_client.py

Open `app/integrations/s3_client.py` and select the `__init__` method (approx lines 21-45).

```
Generate the fixed version of S3Client.__init__ that:
- Loads AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from os.getenv()
- Raises ValueError at startup if either variable is missing
- Removes all debug log lines that print credential values
- Removes the BACKUP_AWS_CREDENTIALS dictionary
```

Apply the generated code to the file.

---

### Step 7: Fix All Remaining Secrets

```
For every other hardcoded secret you found, generate the os.getenv() replacement.
Show the exact line to change in each file.
Which env var name should each secret use?
```

Apply each fix the agent recommends.

---

### Step 8: Generate .env.example

```
Generate a complete .env.example file for this project.
Include every environment variable we just created.
Use safe placeholder values, not real secrets.
Add a comment explaining each variable.
```

Create the file at the project root:

```bash
# The agent output goes here:
code .env.example
```

---

## ✅ Phase 4: Verify

### Step 9: Confirm No Secrets Remain

```
Scan all the files we just modified and confirm no hardcoded secrets remain.
```

After fixes: count should drop 0 live secrets (only `config/production.yaml` placeholders remain).

---

## 🏆 Success Criteria

- [ ] No AWS credentials remain in Python source files
- [ ] No JWT secret in `jwt_handler.py`
- [ ] No admin password in `admin_setup.py`
- [ ] `.env.example` created with all required variables
- [ ] detect-secrets reports 0 live credentials in app code

---

## 📚 Key Takeaway

> Every secret that can be read by anyone with repo access is a secret that can be leaked.  
> `os.getenv("VAR_NAME")` with startup validation is the only safe pattern.

---

## 🔎 Bonus: Discover Secrets with `/plugin advanced-security`

> Based on [Exercise 02 — Discover: Secret Scanning + VS Code Code Review] `/plugin advanced-security`

Use two Copilot IDE security tools to **discover** credentials and surface code issues without leaving the editor — before writing a single fix.

### Install the `advanced-security` plugin

Open Copilot Chat (`Ctrl+Alt+I`), type `/plugins` and install `advanced-security` — or go to **Settings → Plugins → Marketplace** and activate it. This enables GitHub’s credential detection patterns in the IDE.


**Verify checklist:**
- [ ] `advanced-security` plugin installed and active
- [ ] Secret scanning flagged `SECRET_KEY`, `JWT_SECRET`, and AWS credentials
- [ ] Selection review on `login()` flagged SQL injection f-string
- [ ] Uncommitted changes review generated inline comments across changed files
- [ ] OWASP copilot-instructions created (optional)

---

**Next:** [Exercise S2 — Fix SQL Injection](Exercise-S2-SQL-Injection.md)

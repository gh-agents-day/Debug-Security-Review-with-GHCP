# TaskForce Pro Security Workshop
---

## 🎯 Workshop Overview

**Title:** Secure Enterprise Development with GitHub Copilot Agents  
**Platform:** TaskForce Pro - Enterprise Task Management System  
**Company:** GlobalTech Industries (Fortune 100)  
**Duration:** 4–6 hours (can be split across sessions)  
**Difficulty:** Intermediate  
**Prerequisites:** Basic Python, FastAPI, Git knowledge

---

## 🤖 Agent-Driven Approach

This workshop uses **custom Copilot agents**. Each exercise has a dedicated agent pre-created in `.github/copilot-agents/`. You activate the agent once per exercise and drive every discovery and fix through it.

### Pre-created Agents

| Agent file | Used in | Purpose |
|-----------|---------|---------|
| `secret-scanner-agent.agent.md` | S1 | Scans for all credential categories |
| `sql-injection-agent.agent.md` | S2 | Finds and fixes injection points |
| `auth-hardening-agent.agent.md` | S3 | Reviews and hardens the auth system |
| `access-control-agent.agent.md` | S4 | Finds IDOR and broken auth |
| `security-audit-agent.agent.md` | S5 | Comprehensive OWASP Top 10 review |

### How to Activate an Agent

1. Open **GitHub Copilot Chat** (`Ctrl+Alt+I`)
2. Click the **agent picker** (sparkle icon / dropdown at top of panel)
3. Select the agent for the current exercise
4. Type natural language — the agent uses the codebase tools to find and fix issues

> All agents use `mode: agent` with `codebase` and `terminalLastCommand` tools.  
> They read the real source files — no manual file references needed.

---

## 📚 Workshop Objectives

Participants will learn to:
1. **Build custom Copilot agents** specialised for security scanning, injection detection, auth review, and access control
2. **Remediate hardcoded secrets** using the Secret Scanner agent
3. **Fix SQL injection vulnerabilities** using the SQL Injection agent
4. **Secure authentication** using the Auth Hardening agent
5. **Fix authorization issues** (IDOR, broken access control) using the Access Control agent
6. **Run a comprehensive security audit** using the Security Audit agent
7. Understand that every agent can be reused on future projects

---

## 🏢 Business Context

TaskForce Pro is an enterprise task management platform used by **15,000 users** across **450 organizations**. On April 15, 2026, a security incident exposed AWS credentials, resulting in:

- **$45,000** unauthorized AWS charges
- **15,000** customer records exposed
- **$2.5M** estimated fines and remediation costs
- **2 hours 15 minutes** service downtime

This workshop recreates that incident in a safe environment to teach security remediation.
---

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.11 or higher
- VS Code with GitHub Copilot extension
- GitHub Copilot subscription

> **No database required.** The app uses SQLite in-memory — no PostgreSQL, Redis, or external services needed.

### Quick Start (3 commands)

```bash
# 1. Navigate to the project
cd enterprise-app/task-management

# 2. Install minimal dependencies
pip install fastapi uvicorn pyjwt pytest httpx
# Optional security tools:
pip install bandit detect-secrets passlib[bcrypt] pip-audit

# 3. Start the app
python main.py
# App runs at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### Environment Variables (optional for workshop start)

```bash
# Copy the template
cp .env.example .env
# Leave values as-is for the workshop (you'll externalise them in Exercise S1/S3)
```

### Running the Tests (RED → GREEN workflow)

```bash
# Run all tests — most will FAIL intentionally at the start
pytest tests/ -v

# Run a specific exercise's tests
pytest tests/test_security_vulnerabilities.py::TestSQLInjection -v
pytest tests/test_security_vulnerabilities.py::TestJWTSecurity -v
pytest tests/test_security_vulnerabilities.py::TestAuthorization -v

# After fixing each exercise, re-run to confirm GREEN
pytest tests/ -v --tb=short
```

Expected at start: **~10 tests failing**. Expected at end: **all passing**.

### Seed Data

The in-memory database is populated automatically on startup with:

| ID | Email | Role | Notes |
|----|-------|------|-------|
| 1 | admin@globaltech.com | admin | Admin account |
| 2 | jsmith@globaltech.com | manager | Project manager |
| 3 | sarah@globaltech.com | developer | Normal user |
| 4 | mike@globaltech.com | developer | Normal user |
| 5 | alice@globaltech.com | viewer | Read-only user |
| 6 | attacker@evil.com | member | **Attacker account for IDOR demos** |

All passwords: `Password123` (until Exercise S3 replaces with bcrypt)

---

## 🤖 Custom Security Agent Setup

The workshop includes a pre-built **Security Audit Agent** that performs automated OWASP analysis using GitHub Copilot's agent mode.

### What the Agent Does

- Scans the codebase for OWASP Top 10 violations
- Reports exact file paths and line numbers for each finding
- Generates working code fixes
- Interprets Bandit/detect-secrets output
- Produces shareable security audit reports

### How to Create It in VS Code

The agent file is already in the repository at `.github/copilot-agents/security-audit-agent.prompt.md`.

If you want to create it from scratch:

1. Create the folder `.github/copilot-agents/` in your project root
2. Create a new file `security-audit-agent.prompt.md`
3. Add this frontmatter at the top:
   ```yaml
   ---
   mode: agent
   description: Security audit agent for OWASP analysis
   tools:
     - codebase
     - terminalLastCommand
   ---
   ```
4. Write your agent instructions below the frontmatter
5. VS Code will automatically detect the agent

### How to Use the Agent

1. Open GitHub Copilot Chat in VS Code (Ctrl+Alt+I)
2. Click the **@** symbol to see available agents
3. Select **security-audit-agent**
4. Type your prompt:

```
@security-audit-agent Perform a full security audit of this codebase

---

## 🐛 Vulnerability Inventory

### Critical (P0) — 8 Vulnerabilities
| ID | Type | Location | Impact |
|----|------|----------|--------|
| SEC-001 | Hardcoded AWS Credentials | `app/integrations/s3_client.py:15` | Complete AWS account compromise |
| SEC-002 | SQL Injection | `app/api/task_api.py:89` | Database breach, data exfiltration |
| SEC-003 | JWT Secret Hardcoded | `app/auth/jwt_handler.py:12` | Authentication bypass |
| SEC-004 | IDOR (Authorization) | `app/api/task_api.py:145` | Access to any user's tasks |
| SEC-005 | Admin Password in Code | `app/auth/admin_setup.py:8` | Full system access |
| SEC-006 | Database Password in Config | `config/production.yaml:5` | Database compromise |
| SEC-007 | Insecure Deserialization | `app/utils/cache.py:34` | Remote Code Execution |
| SEC-008 | Debug Mode in Production | `main.py:18` | Information disclosure |

### High (P1) — 12 Vulnerabilities
| ID | Type | Location | Impact |
|----|------|----------|--------|
| SEC-009 | XSS in Task Descriptions | `app/api/task_api.py:67` | Session hijacking |
| SEC-010 | SSRF in Webhooks | `app/integrations/webhook_client.py:45` | Internal network access |
| SEC-011 | Sensitive Data in Logs | `app/core/logging_config.py:28` | PII exposure |
| SEC-012 | No Rate Limiting | `app/api/auth_api.py:34` | Brute force attacks |
| SEC-013 | Weak Password Policy | `app/auth/password_validator.py:12` | Easy account compromise |
| SEC-014 | Missing CSRF Protection | `app/api/task_api.py:*` | State-changing attacks |
| SEC-015 | XXE in File Upload | `app/api/attachment_api.py:78` | File system access |
| SEC-016 | Path Traversal | `app/api/attachment_api.py:95` | Arbitrary file read |
| SEC-017 | Unencrypted Communications | `config/production.yaml:12` | Man-in-the-middle |
| SEC-018 | Session Fixation | `app/auth/session_manager.py:23` | Session hijacking |
| SEC-019 | Information Leakage | `app/api/error_handlers.py:15` | Stack traces exposed |
| SEC-020 | Insufficient Logging | `app/api/task_api.py:*` | Security events not tracked |

### Medium (P2) — 10 Code Quality Issues
| ID | Type | Location | Impact |
|----|------|----------|--------|
| BUG-001 | Race Condition | `app/service/task_service.py:156` | Duplicate task assignments |
| BUG-002 | Memory Leak | `app/integrations/database.py:67` | Connection pool exhaustion |
| BUG-003 | Uncaught Exception | `app/service/notification_service.py:89` | Silent notification failures |
| BUG-004 | N+1 Query Problem | `app/api/project_api.py:123` | Slow API responses |
| BUG-005 | Async Not Awaited | `app/service/email_service.py:45` | Emails not sent |
| BUG-006 | Circular Dependency | `app/models/` | Import errors |
| BUG-007 | Resource Not Closed | `app/utils/file_handler.py:78` | File descriptor leak |
| BUG-008 | Timezone Issue | `app/utils/date_helper.py:23` | Wrong task deadlines |
| BUG-009 | Integer Overflow | `app/service/analytics_service.py:134` | Incorrect metrics |
| BUG-010 | Null Reference | `app/api/user_api.py:89` | API crashes |

**Total: 8 Critical · 12 High · 10 Medium = 30 issues**
@security-audit-agent Find all SQL injection vulnerabilities
@security-audit-agent Review app/api/task_api.py for access control issues
@security-audit-agent I fixed the login function — verify my changes are secure
```

### Other Available Agents

The repository also includes agents for the debug workshop:

| Agent | Purpose |
|-------|--------|
| `security-audit-agent` | OWASP analysis + fix recommendations |
| `debug-agent` | Root cause analysis from logs + code |
| `root-cause-agent` | Deep execution trace for mysterious bugs |
| `test-generator-agent` | Generate test suites after bug fixes |

---

## 🔗 Related Resources

### Documentation
- [Main README](../README.md) - Complete vulnerability inventory
- [Incident Report](../observability/incident-report-security.md) - Full incident details
- [Exercise Guides](../workshop/) - All workshop exercises
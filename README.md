# TaskForce Pro — Enterprise Task Management Platform

## Overview

**TaskForce Pro** is an enterprise-grade task management platform used by fortune 500 companies to manage projects, assign tasks, and track team productivity. This implementation contains **intentional security vulnerabilities and bugs** for the workshop.

---

## 🧪 Workshop Exercises

| # | Exercise | Difficulty | Time | Vulnerabilities |
|---|----------|------------|------|-----------------|
| S1 | [Secret Scanning & Remediation](workshop/Exercise-S1-Secret-Scanning.md) | Beginner | 30 min | SEC-001, SEC-003, SEC-005, SEC-006 |
| S2 | [Fix SQL Injection](workshop/Exercise-S2-SQL-Injection.md) | Intermediate | 60 min | SEC-002 |
| S3 | [Authentication Hardening](workshop/Exercise-S3-Authentication-Hardening.md) | Intermediate | 60 min | SEC-003, SEC-005, SEC-011–013 |
| S4 | [Fix Authorization & IDOR](workshop/Exercise-S4-Authorization-IDOR.md) | Intermediate–Advanced | 60 min | SEC-004, SEC-014, SEC-020 |
| S5 | [Complete Security Audit](workshop/Exercise-S5-Complete-Security-Audit.md) | Advanced | 90 min | SEC-008, SEC-009, SEC-016, SEC-019, BUG-002 |

### Advanced Exercises — Database Debugging (~90 min)

For experienced developers who want to tackle database-layer vulnerabilities.

| # | Exercise | Focus Area | Prerequisites |
|---|----------|-----------|---------------|
| D1 | [Debug Database Security & Performance](workshop/Exercise-D1-Debug-Database-Security-Performance.md) | SQL injection, NULL bugs, missing indexes, data integrity | MS SQL Server, completed M1-M5 |


> Full vulnerability inventory, agent guide, and setup details → [workshop/WORKSHOP_GUIDE.md](workshop/WORKSHOP_GUIDE.md)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- VS Code with GitHub Copilot extension

> **No database required.** The app uses SQLite in-memory — no PostgreSQL, Redis, or Docker needed for the workshop.

### Step 1 — Install dependencies

```bash
# Minimum required to run the app and tests
pip install fastapi uvicorn pyjwt pytest httpx pytest-httpx
```

> Optional security scanning tools used in Exercise S5:
> ```bash
> pip install bandit detect-secrets passlib[bcrypt] pip-audit
> ```

### Step 2 — Start the application

```bash
python main.py
```

Expected output:
```
INFO:     In-memory database initialised with sample data
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 3 — Open in browser

| URL | Purpose |
|-----|---------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/ | Health check |

### Demo Credentials

| Email | Password | Role | Notes |
|-------|----------|------|---------|
| admin@globaltech.com | admin123 | admin | Full access |
| sarah.chen@globaltech.com | Password123 | manager | Project manager |
| mike.rodriguez@globaltech.com | Password123 | developer | Normal user |
| jennifer.park@globaltech.com | Password123 | developer | Normal user |
| attacker@evil.com | hacked | member | **Use for IDOR demos** |

---

## ⚠️ Important Disclaimers

**FOR WORKSHOP USE ONLY**

This application contains intentional security vulnerabilities for educational purposes:
- ❌ DO NOT deploy to production
- ❌ DO NOT use with real customer data
- ❌ DO NOT connect to production AWS accounts
- ❌ DO NOT commit actual secrets to the repository

**Use in isolated training environments only.**

---

## 📚 Learning Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Advanced Security Documentation](https://docs.github.com/en/code-security)
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)

---

## 🤝 Support

See [workshop/WORKSHOP_GUIDE.md](workshop/WORKSHOP_GUIDE.md) · incident report: [observability/incident-report-security.md](observability/incident-report-security.md)

---

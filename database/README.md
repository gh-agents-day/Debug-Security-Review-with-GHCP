# ShopSphere Database Layer — Debugging Workshop

This directory contains the database schema, client code, and workshop materials for the **Database Debugging Exercise** in the ShopSphere platform workshop.

## 📁 Contents

```
database/
├── schema.sql                          # MS SQL Server schema with 13 intentional bugs
├── migrations/                         # Database migration scripts (created during workshop)
└── README.md                          # This file

python-services/checkout-service/app/client/
└── database_client.py                 # Python DB client with 23 intentional bugs

observability/
├── database-logs.txt                   # Production logs showing database issues
└── database-incident-report.md        # Detailed incident analysis

workshop/
└── Exercise-D1-Debug-Database-Security-Performance.md  # Workshop exercise guide
```

## 🎯 Workshop Overview

This advanced exercise adds a **database debugging layer** to the ShopSphere checkout service. Participants will debug:

- **SQL Injection Vulnerabilities** (2 critical)
- **NULL Handling Bugs** (database & application layers)
- **Performance Issues** (missing indexes, slow queries)
- **Data Integrity Violations** (missing constraints)
- **Transaction Management** (race conditions, uncommitted changes)
- **Security Issues** (credential exposure, no TLS)

**Total Bugs:** 36 (13 in schema + 23 in Python client)

## 🚀 Quick Start

### Prerequisites

1. MS SQL Server 2019+ or SQL Server Express
2. Python 3.8+ with pyodbc
3. Completed core workshop exercises M1-M5

### Setup Database

```bash
# Install SQL Server (if needed)
# Windows: Download from https://www.microsoft.com/sql-server/sql-server-downloads
# Linux: Use Docker
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong@Passw0rd" -p 1433:1433 -d mcr.microsoft.com/mssql/server:2019-latest

# Create database
sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -Q "CREATE DATABASE ShopSphere"

# Run schema with intentional bugs
sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -d ShopSphere -i database/schema.sql
```

### Install Python Dependencies

```bash
cd python-services/checkout-service
pip install pyodbc
```

### Run the Workshop Exercise

Follow the step-by-step guide in:
```
workshop/Exercise-D1-Debug-Database-Security-Performance.md
```

## 🐛 Bug Categories

### Critical (P0) — Must Fix Immediately

| Bug | Type | Location | Impact |
|-----|------|----------|--------|
| SQL Injection | Security | `database_client.py:120` | Complete DB compromise |
| SQL Injection | Security | `schema.sql` sp_CreateOrder | Table deletion possible |
| NULL Return | Logic | `schema.sql` sp_GetCustomerDiscount | 68% checkout failure |

### High (P1) — Fix Within Hours

| Bug | Type | Location | Impact |
|-----|------|----------|--------|
| Missing Indexes | Performance | `schema.sql:250-256` | 77x slower queries |
| Missing FK | Integrity | `schema.sql:38` | Orphaned records |
| No Commits | Transaction | `database_client.py:91,178` | Data loss |

### Medium (P2) — Fix Within Days

| Bug | Type | Location | Impact |
|-----|------|----------|--------|
| Missing CHECK | Integrity | `schema.sql:17` | Invalid data |
| Wrong Data Type | Schema | `schema.sql:32` | Cannot store 25% discount |
| Race Condition | Concurrency | `schema.sql` sp_ProcessPayment | Duplicate payments |

### Low (P3) — Next Sprint

| Bug | Type | Location | Impact |
|-----|------|----------|--------|
| Credential Logging | Security | `database_client.py:24` | Secrets in logs |
| No TLS | Security | `database_client.py:293` | Unencrypted traffic |
| Swallowed Exceptions | Logging | Multiple locations | Poor debuggability |

## 🎓 Learning Objectives

After completing this exercise, participants will be able to:

1. **Detect and fix SQL injection** vulnerabilities using parameterized queries
2. **Debug NULL propagation** across database and application layers
3. **Optimize database performance** by creating appropriate indexes
4. **Implement data integrity** using foreign keys and CHECK constraints
5. **Handle transactions correctly** to prevent data loss and race conditions
6. **Apply security best practices** for database connections
7. **Use GitHub Copilot** to identify and fix complex database bugs

## 🔧 Integration with Main Workshop

This exercise extends the existing ShopSphere debugging workshop:

- **Builds on:** Exercises M1-M5 (bug reproduction, log analysis, fixing)
- **Adds:** Database layer debugging scenarios
- **Complements:** Existing application-layer bugs in `checkout_service.py`
- **Introduces:** SQL-specific debugging techniques

### How the Bugs Relate

The database NULL bug (`sp_GetCustomerDiscount` returns NULL) **mirrors** the original workshop bug where `discount_client.py` returns None. This demonstrates:
- How bugs propagate across layers
- Why validation is needed at every boundary
- The importance of NULL handling in distributed systems

## 📊 Workshop Metrics

### Time Investment
- **Setup:** 15 minutes
- **Exercise D1:** 90-120 minutes
- **Total:** ~2 hours

### Difficulty
- **Level:** Advanced
- **Prerequisites:** SQL knowledge, Python, debugging experience
- **Recommended after:** Core exercises M1-M5

### Bug Fix Progression

As participants fix bugs, they'll see measurable improvements:

| Metric | Before | After |
|--------|--------|-------|
| Checkout Failure Rate | 68% | 0% |
| Query Execution Time | 3,847ms | <50ms |
| SQL Injection Tests | ❌ Vulnerable | ✅ Protected |
| Orphaned Records | 15 | 0 |
| Revenue Loss | $18K/min | $0 |

## 🛡️ Security Considerations

⚠️ **IMPORTANT:** This code contains **intentional vulnerabilities** for educational purposes.

**DO NOT:**
- Deploy this code to production
- Use these patterns in real applications
- Expose this database to the internet

**DO:**
- Use this in isolated training environments only
- Learn from the vulnerabilities to prevent them in your code
- Share the security lessons with your team

## 🧪 Testing

Generate and run security tests:

```bash
# Generate tests using Copilot (covered in workshop)
# Run tests
cd python-services/checkout-service
pytest tests/test_database_security.py -v
```

Expected test coverage:
- SQL injection prevention (3 tests)
- NULL handling (3 tests)
- Input validation (2 tests)
- Transaction integrity (2 tests)

## 📚 Additional Resources

### Database Security
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [Database Security Best Practices](https://learn.microsoft.com/en-us/sql/relational-databases/security/security-best-practices)

### Performance Tuning
- [SQL Server Index Design Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide)
- [Execution Plan Analysis](https://learn.microsoft.com/en-us/sql/relational-databases/performance/execution-plans)
- [Query Performance Tuning](https://learn.microsoft.com/en-us/sql/relational-databases/performance/query-performance-tuning)

### Python Database Programming
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)
- [Python DB-API Specification](https://peps.python.org/pep-0249/)
- [SQLAlchemy Best Practices](https://docs.sqlalchemy.org/en/20/faq/performance.html)

## 🤝 Contributing

Have ideas for additional database debugging scenarios? Consider adding:
- NoSQL database bugs (MongoDB, Cosmos DB)
- ORM-specific issues (SQLAlchemy, Entity Framework)
- Database migration challenges
- Replication and failover bugs

## 📝 Feedback

We'd love to hear about your experience with this exercise:
- How long did it take?
- Which bugs were hardest to find?
- What would you add or change?
- Did GitHub Copilot help you find bugs faster?

## 🏆 Credits

Created for the **GitHub Copilot Debugging Workshop**  
Part of the ShopSphere e-commerce platform training materials  

---

**Happy Debugging! 🐛🔍**

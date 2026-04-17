# ShopSphere Database Security & Performance Incident
# Incident ID: INC-20260415-1445
# Severity: P0 (Critical Security & Revenue Impact)
# Started: 2026-04-15 14:23 UTC

## Executive Summary
**CRITICAL SECURITY BREACH** — Multiple SQL injection vulnerabilities discovered in production database layer, combined with severe data integrity violations and performance degradation. Checkout service failure rate: 68%. Revenue impact: $18,000/minute.

---

## Incident Timeline

### 14:23 UTC — First Symptoms Detected
- Checkout failures begin appearing
- TypeError: NoneType errors in discount calculation
- Similar pattern to previous incident (INC-20260410-0247)

### 14:23 UTC — Performance Degradation Observed
- Query execution times exceed 3+ seconds
- Database connection pool at 95% utilization
- Full table scans detected on PaymentAuditLog (2.4M rows)

### 14:23 UTC — SECURITY BREACH DETECTED
- **SQL injection attack successfully executed via customer search**
- Attacker input: `' OR '1'='1` exposed all 8,524 orders
- Second attack via order creation endpoint attempted table deletion
- Attack blocked by database permissions (defense in depth)

### 14:24 UTC — Data Integrity Violations Confirmed
- 15 orphaned orders with invalid CustomerId references
- Loyalty point calculation errors (customers receiving 6x expected points)
- 350 loyalty updates lost due to missing transaction commits

### 14:24 UTC — P0 Escalation
- All hands on deck called
- Revenue loss projection: $2.16M if not resolved in 2 hours

---

## Root Causes Identified

### 🔴 CRITICAL: SQL Injection Vulnerabilities

#### Vulnerability #1: Customer Search (database_client.py)
```python
# Line 120-127 — VULNERABLE CODE
query = f"""
    SELECT o.OrderId, o.OrderDate...
    FROM Orders o
    INNER JOIN Customers c ON o.CustomerId = c.CustomerId
    WHERE c.Email = '{email}'  -- <-- String concatenation!
"""
cursor.execute(query)
```

**Attack Vector:** Any user input in `email` parameter executes arbitrary SQL
**Exploit Example:**
- Input: `' OR '1'='1` → Returns ALL orders
- Input: `'; DROP TABLE Orders; --` → Deletes Orders table
- Input: `' UNION SELECT * FROM Customers --` → Data exfiltration

#### Vulnerability #2: Order Creation (schema.sql)
```sql
-- sp_CreateOrder lines 145-150 — VULNERABLE STORED PROCEDURE
SET @SQL = 'INSERT INTO Orders (...) VALUES (' + 
           CAST(@CustomerId AS NVARCHAR) + ', ' + 
           ... + ', ''' + @OrderStatus + ''', ''Pending'')';
EXEC sp_executesql @SQL;
```

**Attack Vector:** `@OrderStatus` parameter allows SQL injection
**Exploit Example:**
- Input: `Confirmed'); DROP TABLE Orders; --`
- Input: `Pending'); UPDATE Orders SET PaymentStatus='Completed' WHERE 1=1; --`

---

### 🟠 HIGH: NULL Handling Bug (Database Layer)

#### Bug: Stored Procedure Returns NULL Instead of 0

**File:** `database/schema.sql` — `sp_GetCustomerDiscount` (lines 78-100)

```sql
-- Bug #6: No NULL check for missing customer
SELECT @LoyaltyTier = LoyaltyTier
FROM Customers
WHERE CustomerId = @CustomerId;
-- If customer doesn't exist, @LoyaltyTier is NULL

-- Bug #7: NULL returned instead of 0 when no discount
IF @DiscountPct IS NOT NULL
    SET @DiscountAmount = @PurchaseAmount * (@DiscountPct / 100.0);
ELSE IF @FixedDiscount IS NOT NULL
    SET @DiscountAmount = @FixedDiscount;
ELSE
    SET @DiscountAmount = NULL;  -- <-- Should be 0
```

**Impact:** 
- Python code receives `None` from database
- `amount - None` raises TypeError
- Same bug pattern as original workshop incident, now in database

---

### 🟠 HIGH: Performance Issues

#### Missing Indexes Causing Full Table Scans

**Affected Queries:**
1. `PaymentAuditLog` lookups by `OrderId` — 2.4M row table scan
2. `OrderItems` joins on `OrderId` — O(n²) complexity
3. Customer order history queries — no index on `Orders.CustomerId`

**Measured Impact:**
- Query times: 3,847ms (should be <50ms)
- Connection pool exhaustion
- Revenue-impacting checkout delays

**Required Indexes (commented out in schema.sql):**
```sql
-- Lines 250-256 — COMMENTED OUT (Bug #4)
-- CREATE INDEX IX_Orders_CustomerId ON Orders(CustomerId);
-- CREATE INDEX IX_OrderItems_OrderId ON OrderItems(OrderId);
-- CREATE INDEX IX_PaymentAuditLog_OrderId ON PaymentAuditLog(OrderId);
```

---

### 🟡 MEDIUM: Data Integrity Violations

#### Missing Foreign Key Constraint
**File:** `schema.sql` line 38 (Bug #3)
```sql
CREATE TABLE Orders (
    OrderId INT PRIMARY KEY IDENTITY(1,1),
    CustomerId INT NOT NULL,
    -- Missing: FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId)
```
**Impact:** 15 orphaned orders with `CustomerId=999` (customer doesn't exist)

#### Missing CHECK Constraint
**File:** `schema.sql` line 17 (Bug #1)
```sql
LoyaltyTier NVARCHAR(20) DEFAULT 'Bronze',
-- Missing: CHECK (LoyaltyTier IN ('Bronze', 'Silver', 'Gold', 'Platinum'))
```
**Impact:** Invalid tier `'SuperAdmin'` inserted successfully

#### Incorrect Data Type for Discount Percentage
**File:** `schema.sql` line 32 (Bug #2)
```sql
DiscountPercentage DECIMAL(3,2),  -- Max value: 9.99
-- Should be: DECIMAL(5,2)        -- Max value: 999.99
```
**Impact:** Cannot store 25% discount, data truncation errors

---

### 🟡 MEDIUM: Transaction & Concurrency Issues

#### No Transaction Isolation in Payment Processing
**File:** `schema.sql` — `sp_ProcessPayment` (lines 170-195)
```sql
-- Bug #9: Missing BEGIN TRANSACTION
CREATE PROCEDURE sp_ProcessPayment ...
AS
BEGIN
    SET NOCOUNT ON;
    -- No transaction boundary!
    INSERT INTO PaymentAuditLog ...
    UPDATE Orders ...
END;
```
**Impact:** Race condition allows duplicate payments for same order

#### Missing Commit Calls in Python Client
**File:** `database_client.py` lines 85, 150 (Bugs #8, #15)
```python
cursor.execute("{CALL sp_CreateOrder (...)}")
order_id = cursor.fetchval()
cursor.close()
# Missing: self.connection.commit()
```
**Impact:** 350 loyalty point updates lost when connection closed

---

### 🟡 MEDIUM: Logic Error in Loyalty Points Calculation

#### Bug: Uses >= Instead of = for Tier Comparison
**File:** `schema.sql` — `fn_CalculateLoyaltyPoints` (lines 230-245)
```sql
-- Bug #13: Cumulative instead of exclusive tiers
IF @LoyaltyTier >= 'Platinum'
    SET @Points = CAST(@PurchaseAmount * 5 AS INT);
IF @LoyaltyTier >= 'Gold'           -- Also executes for Platinum!
    SET @Points = CAST(@PurchaseAmount * 3 AS INT);
IF @LoyaltyTier >= 'Silver'         -- Also executes for Gold/Platinum!
    SET @Points = CAST(@PurchaseAmount * 2 AS INT);
```
**Impact:** Gold customers getting 6x points (1+2+3 instead of 3)

---

### 🔵 LOW: Security & Logging Issues

#### Credentials Logged in Plaintext
**File:** `database_client.py` line 24 (Bug #1)
```python
logger.info(f"Initializing database connection: {connection_string}")
# Logs: ...PWD=P@ssw0rd123!
```

#### No TLS/SSL Enforcement
**File:** `database_client.py` line 293 (Bug #23)
```python
# Missing: Encrypt=yes;TrustServerCertificate=no
return f"DRIVER=...; UID={username}; PWD={password}"
```

#### Swallowed Exceptions
**File:** `database_client.py` — Multiple locations (Bugs #2, #5, #16, #21)
```python
except Exception as e:
    logger.error("Failed to get customer discount")
    # No exc_info=True, no re-raise
    return None
```

---

## Complete Bug Inventory (Database Layer)

### Schema Bugs (schema.sql)
| Bug # | Severity | Type | Line | Description |
|-------|----------|------|------|-------------|
| 1 | Medium | Integrity | 17 | Missing CHECK constraint on LoyaltyTier |
| 2 | Medium | Data Type | 32 | DECIMAL(3,2) too small for percentages |
| 3 | High | Integrity | 38 | Missing foreign key Orders→Customers |
| 4 | High | Performance | 56 | Missing index on OrderItems.OrderId |
| 5 | High | Performance | 70 | Missing indexes on PaymentAuditLog |
| 6 | High | NULL | 89 | No NULL check for missing customer |
| 7 | High | NULL | 100 | Returns NULL instead of 0 for no discount |
| 8 | Critical | SQL Injection | 145 | Dynamic SQL with string concatenation |
| 9 | Medium | Concurrency | 170 | Missing transaction isolation |
| 10 | Medium | Logic | 193 | No ELSE for failed payments |
| 11 | Low | Logic | 210 | COUNT without NULL check |
| 12 | Medium | Integrity | 217 | LEFT JOIN allows orphaned orders |
| 13 | Medium | Logic | 235 | >= instead of = in tier comparison |

### Python Client Bugs (database_client.py)
| Bug # | Severity | Type | Line | Description |
|-------|----------|------|------|-------------|
| 1 | Low | Security | 24 | Connection string logged in plaintext |
| 2 | High | Error | 35 | Connection exception not re-raised |
| 3 | High | NULL | 54 | Returns NULL from stored procedure |
| 4 | High | NULL | 57 | No NULL check before return |
| 5 | Medium | Error | 61 | Returns None on error (ambiguous) |
| 6 | **Critical** | **SQL Injection** | 77 | order_status passed to vulnerable SP |
| 7 | High | Validation | 79 | No input validation on order_status |
| 8 | High | Transaction | 91 | Missing commit call |
| 9 | Medium | Error | 98 | Only catches pyodbc.Error |
| 10 | **Critical** | **SQL Injection** | 120 | String concatenation in WHERE clause |
| 11 | Medium | Performance | 133 | No result limit (unbounded query) |
| 12 | Medium | Error | 151 | Empty list on error (ambiguous) |
| 13 | Medium | Concurrency | 165 | Race condition on payments |
| 14 | Medium | Validation | 172 | No order existence check |
| 15 | High | Transaction | 178 | Missing commit call |
| 16 | Medium | Error | 183 | Swallows exception |
| 17 | High | Performance | 200 | Slow query from missing index |
| 18 | Medium | Logging | 224 | Exception details not logged |
| 19 | High | Transaction | 233 | No transaction handling |
| 20 | High | Validation | 233 | Negative points not prevented |
| 21 | High | Error | 250 | Exception swallowed via pass |
| 22 | Medium | Security | 286 | Hardcoded credentials |
| 23 | Medium | Security | 293 | No TLS/SSL enforcement |

**Total Bugs: 36 (13 schema + 23 Python client)**

---

## Impact Assessment

### Security Impact
- **SQL Injection:** Complete database compromise possible
- **Data Exfiltration:** All customer orders exposed in first attack
- **Authentication:** Credentials exposed in logs
- **Encryption:** Database traffic not encrypted

### Financial Impact
- Checkout failure rate: **68%**
- Revenue loss: **$18,000/minute**
- Projected 2-hour fix time: **$2.16M total loss**
- Compliance fines (data breach): **$500K - $2M**

### Data Integrity Impact
- 15 orphaned orders (invalid references)
- 350 lost loyalty point updates
- Incorrect points awarded (6x multiplier bug)
- Unknown number of unreported payment failures

### Performance Impact
- Query times: 3,847ms (77x slower than target)
- Connection pool exhausted (95% utilization)
- Full table scans on 2.4M row table
- Production database CPU at 92%

---

## Immediate Actions Required

1. **CRITICAL:** Deploy SQL injection fixes
   - Parameterize all queries in `database_client.py`
   - Rewrite `sp_CreateOrder` without dynamic SQL
   
2. **HIGH:** Fix NULL handling
   - Update `sp_GetCustomerDiscount` to return 0 instead of NULL
   - Add NULL checks in Python client
   
3. **HIGH:** Deploy missing indexes
   - Uncomment lines 250-256 in `schema.sql`
   - Run index creation during maintenance window
   
4. **MEDIUM:** Fix data integrity
   - Add foreign key constraint (requires orphan cleanup first)
   - Add CHECK constraint on LoyaltyTier
   - Fix DECIMAL precision for discount percentage

5. **MEDIUM:** Add transaction handling
   - Wrap `sp_ProcessPayment` in BEGIN TRANSACTION
   - Add commit calls in Python client
   
6. **LOW:** Security hardening
   - Enable TLS/SSL for database connections
   - Remove credential logging
   - Implement connection string encryption

---

## Testing Validation Checklist

After fixes deployed:
- [ ] SQL injection tests return errors (not data)
- [ ] NULL discount returns 0 (not None)
- [ ] Query execution < 100ms
- [ ] Orphaned orders blocked by FK constraint
- [ ] Payment audit logs committed
- [ ] Credentials not in logs
- [ ] TLS enabled for DB connections
- [ ] Transaction isolation prevents race conditions

---

## Prevention Recommendations

1. **Code Review:** Mandatory security review for all DB code
2. **Static Analysis:** Enable SQL injection detection tools
3. **Testing:** Add integration tests with attack vectors
4. **Monitoring:** Alert on slow queries (>100ms threshold)
5. **Schema:** Enforce constraints in CREATE TABLE statements
6. **Training:** Database security workshop for all engineers

---

## Workshop Learning Objectives

This incident demonstrates:
- SQL injection vulnerabilities in real-world applications
- Importance of parameterized queries and stored procedure safety
- NULL handling bugs propagating across layers
- Performance impact of missing indexes
- Data integrity violations from missing constraints
- Transaction management and concurrency issues
- Defensive logging and error handling

**Time to complete fixes:** 2-3 hours
**Difficulty:** Advanced (requires database and application code changes)

# Exercise D1: Debug Database Schema, Queries & Procedures
## ShopSphere Database Security & Performance Workshop

**Objective:** Debug SQL injection vulnerabilities, schema integrity issues, NULL handling bugs, and performance problems in the ShopSphere database layer.

**Estimated Time:** 90-120 minutes

**Prerequisites:** 
- Completed core exercises M1-M5 OR exercises 01-11
- Understanding of SQL Server and Python database clients
- Basic knowledge of SQL injection and database security

---

## 🎯 What You'll Learn

In this advanced exercise, you'll use GitHub Copilot to:
1. **Detect and fix SQL injection vulnerabilities** in queries and stored procedures
2. **Debug NULL handling bugs** that propagate from database to application
3. **Fix data integrity issues** (missing foreign keys, constraints)
4. **Optimize performance** by adding missing indexes
5. **Implement proper transaction handling** to prevent race conditions
6. **Apply security best practices** (TLS, credential management, logging)

---

## 📋 Scenario

A **critical security breach** has been detected in the ShopSphere database layer:
- SQL injection attacks successfully executed
- 68% checkout failure rate due to NULL handling bugs
- Severe performance degradation from missing indexes
- Data integrity violations (orphaned records, invalid data)
- $18,000/minute revenue loss

You are the on-call engineer. Your mission: **identify and fix all database vulnerabilities before the 2-hour SLA expires.**

---

## 🚀 Setup

### Step 1: Review the Database Schema

```bash
# Open the database schema file
code database/schema.sql
```

**📝 Prompt for Copilot Chat:**
```
@workspace Review the database schema in #file:schema.sql and identify all intentional bugs. 
Create a categorized list of:
1. Security vulnerabilities (SQL injection, credential exposure)
2. Data integrity issues (missing constraints, foreign keys)
3. Performance problems (missing indexes)
4. Logic errors (NULL handling, calculation bugs)

For each bug, provide the line number and severity.
```

<details>
<summary>✅ Expected Result</summary>

Copilot should identify:
- **13 bugs in schema.sql** (SQL injection, missing indexes, NULL returns, integrity issues)
- **23 bugs in database_client.py** (SQL injection, missing commits, exception handling)
- Total: **36 bugs** to fix

</details>

---

### Step 2: Review the Database Client

```bash
# Open the Python database client
code python-services/checkout-service/app/client/database_client.py
```

**📝 Prompt for Copilot Chat:**
```
#file:database_client.py contains SQL injection vulnerabilities and transaction bugs.

Identify all locations where:
1. User input is concatenated into SQL queries (SQL injection)
2. Transactions are not committed (data loss risk)
3. Exceptions are swallowed without proper logging
4. NULL values are returned without validation

Show me the vulnerable code snippets and explain the attack vectors.
```

<details>
<summary>✅ Expected Result</summary>

Copilot should highlight:
- **Line 120-127:** SQL injection in `search_orders_by_customer`
- **Line 77-95:** SQL injection via `sp_CreateOrder`
- **Lines 91, 178:** Missing commit calls
- **Lines 57, 61:** NULL returned without checks

</details>

---

## 🔍 Phase 1: Analyze the Database Incident

### Step 3: Read the Database Incident Report

Open the incident report and logs:
```bash
code observability/database-incident-report.md
code observability/database-logs.txt
```

**📝 Prompt for Copilot Chat:**
```
Read #file:database-incident-report.md and #file:database-logs.txt

Summarize the incident timeline and create a prioritized fix list:
1. CRITICAL (P0): Fixes that must be deployed immediately (security, revenue impact)
2. HIGH (P1): Fixes needed within hours (data integrity, major bugs)
3. MEDIUM (P2): Fixes needed within days (performance, minor bugs)
4. LOW (P3): Improvements for next sprint (logging, hardening)

For each priority level, list the specific files and line numbers to fix.
```

<details>
<summary>✅ Expected Result</summary>

**CRITICAL (P0):**
- Fix SQL injection in `database_client.py` lines 120-127, 77-95
- Fix SQL injection in `schema.sql` `sp_CreateOrder` procedure
- Fix NULL handling in `sp_GetCustomerDiscount` and Python client

**HIGH (P1):**
- Add missing indexes (`schema.sql` lines 250-256)
- Add missing foreign key constraint (line 38)
- Add transaction commits in Python client

</details>

---

## 🛠️ Phase 2: Fix Critical Security Vulnerabilities

### Step 4: Fix SQL Injection in Customer Search

**📝 Prompt for Copilot Chat:**
```
@workspace Fix the SQL injection vulnerability in database_client.py method search_orders_by_customer (lines 120-127).

Replace string concatenation with parameterized queries.
Show me the fixed code.
```

<details>
<summary>✅ Expected Fix</summary>

```python
def search_orders_by_customer(self, email: str) -> List[Dict]:
    try:
        cursor = self.connection.cursor()
        
        # FIXED: Use parameterized query instead of string concatenation
        query = """
            SELECT o.OrderId, o.OrderDate, o.TotalAmount, o.FinalAmount, 
                   o.OrderStatus, o.PaymentStatus
            FROM Orders o
            INNER JOIN Customers c ON o.CustomerId = c.CustomerId
            WHERE c.Email = ?
            ORDER BY o.OrderDate DESC
        """
        
        cursor.execute(query, (email,))  # Use parameter tuple
        # ... rest of method
```

</details>

**Apply the fix:**
1. Select the vulnerable code (lines 120-135)
2. Use inline chat: `/fix SQL injection - use parameterized query`
3. Review and accept the fix
4. Verify the `?` placeholder and parameter tuple are correct

---

### Step 5: Fix SQL Injection in Stored Procedure

**📝 Prompt for Copilot Chat:**
```
#file:schema.sql The stored procedure sp_CreateOrder (lines 110-125) uses dynamic SQL 
with string concatenation, making it vulnerable to SQL injection.

Rewrite this procedure to use parameterized INSERT instead of sp_executesql with concatenated strings.
```

<details>
<summary>✅ Expected Fix</summary>

```sql
CREATE PROCEDURE sp_CreateOrder
    @CustomerId INT,
    @TotalAmount DECIMAL(10,2),
    @DiscountAmount DECIMAL(10,2),
    @OrderStatus NVARCHAR(20),
    @OrderId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- FIXED: Direct parameterized INSERT instead of dynamic SQL
    INSERT INTO Orders (CustomerId, TotalAmount, DiscountAmount, FinalAmount, OrderStatus, PaymentStatus)
    VALUES (@CustomerId, @TotalAmount, @DiscountAmount, @TotalAmount - @DiscountAmount, @OrderStatus, 'Pending');
    
    SET @OrderId = SCOPE_IDENTITY();
END;
```

</details>

**Apply the fix:**
- Select the entire `sp_CreateOrder` procedure
- Use inline chat: `/fix remove dynamic SQL, use direct INSERT`
- Verify no string concatenation remains

---

### Step 6: Add Input Validation

**📝 Prompt for Copilot Chat:**
```
In database_client.py method create_order (line 77), add input validation for order_status.

Only allow: 'Pending', 'Processing', 'Confirmed', 'Failed'
Raise ValueError if invalid status is provided.
```

<details>
<summary>✅ Expected Fix</summary>

```python
def create_order(
    self,
    customer_id: int,
    total_amount: float,
    discount_amount: float,
    order_status: str = "Pending"
) -> Optional[int]:
    try:
        # FIXED: Input validation
        VALID_STATUSES = {'Pending', 'Processing', 'Confirmed', 'Failed'}
        if order_status not in VALID_STATUSES:
            raise ValueError(f"Invalid order_status: {order_status}. Must be one of {VALID_STATUSES}")
        
        # ... rest of method
```

</details>

**Apply the fix:**
- Place cursor at line 77
- Use inline chat: `/fix add validation for order_status parameter`

---

## 🐛 Phase 3: Fix NULL Handling Bugs

### Step 7: Fix Stored Procedure NULL Return

**📝 Prompt for Copilot Chat:**
```
#file:schema.sql The stored procedure sp_GetCustomerDiscount has two NULL-related bugs:

Bug #6 (line 89): No NULL check for @LoyaltyTier when customer doesn't exist
Bug #7 (line 100): Returns NULL instead of 0 when no discount applies

Fix both bugs:
1. Add IF @LoyaltyTier IS NULL check and set @DiscountAmount = 0
2. Change final ELSE to SET @DiscountAmount = 0 instead of NULL
```

<details>
<summary>✅ Expected Fix</summary>

```sql
CREATE PROCEDURE sp_GetCustomerDiscount
    @CustomerId INT,
    @PurchaseAmount DECIMAL(10,2),
    @DiscountAmount DECIMAL(10,2) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @LoyaltyTier NVARCHAR(20);
    DECLARE @DiscountPct DECIMAL(5,2);
    DECLARE @FixedDiscount DECIMAL(10,2);
    
    -- Get customer loyalty tier
    SELECT @LoyaltyTier = LoyaltyTier
    FROM Customers
    WHERE CustomerId = @CustomerId;
    
    -- FIXED Bug #6: Check if customer exists
    IF @LoyaltyTier IS NULL
    BEGIN
        SET @DiscountAmount = 0;
        RETURN;
    END
    
    -- Find applicable discount rule
    SELECT TOP 1 
        @DiscountPct = DiscountPercentage,
        @FixedDiscount = DiscountFixedAmount
    FROM DiscountRules
    WHERE LoyaltyTier = @LoyaltyTier
        AND MinPurchaseAmount <= @PurchaseAmount
        AND IsActive = 1
        AND GETUTCDATE() BETWEEN ValidFrom AND ValidUntil
    ORDER BY MinPurchaseAmount DESC;
    
    -- Calculate discount
    IF @DiscountPct IS NOT NULL
        SET @DiscountAmount = @PurchaseAmount * (@DiscountPct / 100.0);
    ELSE IF @FixedDiscount IS NOT NULL
        SET @DiscountAmount = @FixedDiscount;
    ELSE
        SET @DiscountAmount = 0;  -- FIXED Bug #7: Return 0 instead of NULL
END;
```

</details>

**Apply the fix:**
- Select the entire `sp_GetCustomerDiscount` procedure
- Use inline chat: `/fix return 0 instead of NULL for no discount`

---

### Step 8: Add NULL Checks in Python Client

**📝 Prompt for Copilot Chat:**
```
In database_client.py method get_customer_discount (lines 40-61):

Add validation to ensure the returned discount is never None.
If the stored procedure returns None, log an error and return 0.0 instead.
Use logger.error with exc_info=True if this happens.
```

<details>
<summary>✅ Expected Fix</summary>

```python
def get_customer_discount(self, customer_id: int, purchase_amount: float) -> float:
    try:
        cursor = self.connection.cursor()
        
        discount_amount = cursor.execute(
            "{CALL sp_GetCustomerDiscount (?, ?, ?)}",
            (customer_id, purchase_amount, None)
        ).fetchval()
        
        cursor.close()
        
        # FIXED: Validate discount is not None
        if discount_amount is None:
            logger.error(
                f"Stored procedure returned NULL for customer_id={customer_id}. Defaulting to 0.",
                exc_info=True
            )
            return 0.0
        
        return discount_amount
        
    except Exception as e:
        logger.error(f"Failed to get customer discount: {e}", exc_info=True)
        return 0.0  # FIXED: Return 0 instead of None on error
```

**Note:** Change return type annotation from `Optional[float]` to `float`

</details>

---

## ⚡ Phase 4: Fix Performance Issues

### Step 9: Create Missing Indexes

**📝 Prompt for Copilot Chat:**
```
#file:schema.sql Lines 250-256 contain commented-out index creation statements.

Uncomment and explain why each index is critical for performance.
Which queries will benefit from each index?
```

**Apply the fix:**
- Select lines 250-256 in `schema.sql`
- Uncomment all CREATE INDEX statements
- Save the file

<details>
<summary>✅ Expected Indexes</summary>

```sql
-- PERFORMANCE CRITICAL: These indexes are required for production
CREATE INDEX IX_Orders_CustomerId ON Orders(CustomerId);
CREATE INDEX IX_Orders_OrderDate ON Orders(OrderDate);
CREATE INDEX IX_OrderItems_OrderId ON OrderItems(OrderId);
CREATE INDEX IX_PaymentAuditLog_OrderId ON PaymentAuditLog(OrderId);
CREATE INDEX IX_PaymentAuditLog_TransactionId ON PaymentAuditLog(TransactionId);
CREATE INDEX IX_Customers_LoyaltyTier ON Customers(LoyaltyTier);
```

**Impact:** Query times will drop from 3,847ms → <50ms

</details>

---

### Step 10: Add Query Result Limit

**📝 Prompt for Copilot Chat:**
```
In database_client.py method search_orders_by_customer (line 120):

Add a result limit to prevent returning millions of rows.
Limit to 100 most recent orders.
Modify the SQL query to include TOP 100.
```

<details>
<summary>✅ Expected Fix</summary>

```python
query = """
    SELECT TOP 100 o.OrderId, o.OrderDate, o.TotalAmount, o.FinalAmount, 
           o.OrderStatus, o.PaymentStatus
    FROM Orders o
    INNER JOIN Customers c ON o.CustomerId = c.CustomerId
    WHERE c.Email = ?
    ORDER BY o.OrderDate DESC
"""
```

</details>

---

## 🔒 Phase 5: Fix Data Integrity Issues

### Step 11: Add Foreign Key Constraint

**📝 Prompt for Copilot Chat:**
```
#file:schema.sql The Orders table (line 38) is missing a foreign key constraint to Customers.

This allows orphaned orders with invalid CustomerId values.

Generate the ALTER TABLE statement to add this constraint.
Note: Existing orphaned orders must be cleaned up first.
```

<details>
<summary>✅ Expected Fix</summary>

```sql
-- Step 1: Clean up orphaned orders first
DELETE FROM Orders WHERE CustomerId NOT IN (SELECT CustomerId FROM Customers);

-- Step 2: Add foreign key constraint
ALTER TABLE Orders
ADD CONSTRAINT FK_Orders_Customers 
FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId);
```

</details>

**Apply the fix:**
- Add these statements to the end of `schema.sql`
- Or create a new migration file: `database/migrations/001_add_foreign_keys.sql`

---

### Step 12: Add CHECK Constraint

**📝 Prompt for Copilot Chat:**
```
#file:schema.sql The Customers table (line 17) allows invalid LoyaltyTier values.

Add a CHECK constraint to only allow: 'Bronze', 'Silver', 'Gold', 'Platinum'

Show me the ALTER TABLE statement.
```

<details>
<summary>✅ Expected Fix</summary>

```sql
ALTER TABLE Customers
ADD CONSTRAINT CK_Customers_LoyaltyTier 
CHECK (LoyaltyTier IN ('Bronze', 'Silver', 'Gold', 'Platinum'));
```

</details>

---

### Step 13: Fix Discount Percentage Data Type

**📝 Prompt for Copilot Chat:**
```
#file:schema.sql Line 32: DiscountPercentage DECIMAL(3,2) only supports values up to 9.99.

This prevents storing 25% discounts.

Generate ALTER TABLE to change it to DECIMAL(5,2).
```

<details>
<summary>✅ Expected Fix</summary>

```sql
ALTER TABLE DiscountRules
ALTER COLUMN DiscountPercentage DECIMAL(5,2);
```

</details>

---

## 🔄 Phase 6: Fix Transaction Handling

### Step 14: Add Transaction to Stored Procedure

**📝 Prompt for Copilot Chat:**
```
#file:schema.sql The sp_ProcessPayment procedure (lines 170-195) has no transaction handling.

This causes race conditions where multiple payments can be processed for the same order.

Wrap the procedure body in BEGIN TRANSACTION / COMMIT TRANSACTION.
Add ROLLBACK on error.
```

<details>
<summary>✅ Expected Fix</summary>

```sql
CREATE PROCEDURE sp_ProcessPayment
    @OrderId INT,
    @PaymentAmount DECIMAL(10,2),
    @PaymentMethod NVARCHAR(50),
    @TransactionId NVARCHAR(100),
    @Success BIT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- FIXED: Add transaction boundary
    BEGIN TRANSACTION;
    
    BEGIN TRY
        DECLARE @StartTime DATETIME2 = GETUTCDATE();
        
        -- Log the payment attempt
        INSERT INTO PaymentAuditLog (OrderId, PaymentAmount, PaymentMethod, TransactionId, Status, ProcessingTimeMs)
        VALUES (@OrderId, @PaymentAmount, @PaymentMethod, @TransactionId, 
                CASE WHEN @Success = 1 THEN 'Success' ELSE 'Failed' END,
                DATEDIFF(MILLISECOND, @StartTime, GETUTCDATE()));
        
        -- Update order based on payment result
        IF @Success = 1
        BEGIN
            UPDATE Orders
            SET PaymentStatus = 'Completed',
                OrderStatus = 'Confirmed'
            WHERE OrderId = @OrderId;
        END
        ELSE
        BEGIN
            -- FIXED Bug #10: Handle failed payments
            UPDATE Orders
            SET PaymentStatus = 'Failed',
                OrderStatus = 'Failed'
            WHERE OrderId = @OrderId;
        END
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
```

</details>

---

### Step 15: Add Commit Calls in Python Client

**📝 Prompt for Copilot Chat:**
```
In database_client.py, these methods are missing commit calls:
- create_order (line 91)
- log_payment_attempt (line 178)

Add self.connection.commit() after cursor.close() in both methods.
```

**Apply the fix:**
- Find each location
- Add commit call after the cursor operations
- Use inline chat: `/fix add transaction commit`

---

## 🛡️ Phase 7: Security Hardening

### Step 16: Remove Credential Logging

**📝 Prompt for Copilot Chat:**
```
database_client.py line 24 logs the connection string, which includes plaintext credentials.

Remove this log statement or redact the password before logging.
```

<details>
<summary>✅ Expected Fix</summary>

```python
def __init__(self, connection_string: str):
    self.connection_string = connection_string
    # FIXED: Don't log connection string with credentials
    logger.info("Initializing database connection")
    self.connection = None
```

</details>

---

### Step 17: Enable TLS/SSL

**📝 Prompt for Copilot Chat:**
```
#file:database_client.py The build_connection_string function (line 278) doesn't enforce TLS encryption.

Add these parameters to the connection string:
- Encrypt=yes
- TrustServerCertificate=no

Show me the updated function.
```

<details>
<summary>✅ Expected Fix</summary>

```python
def build_connection_string(
    server: str,
    database: str,
    username: str,
    password: str,
    driver: str = "ODBC Driver 17 for SQL Server"
) -> str:
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"  # FIXED: Enable TLS
        f"TrustServerCertificate=no"  # FIXED: Validate server certificate
    )
```

</details>

---

### Step 18: Fix Exception Logging

**📝 Prompt for Copilot Chat:**
```
@workspace In database_client.py, find all logger.error() calls that don't include exc_info=True.

These should log the full exception traceback for debugging.

Add exc_info=True to all exception logging statements.
```

**Apply the fix:**
- Use Find & Replace or multi-cursor editing
- Change `logger.error("...")` to `logger.error("...", exc_info=True)` in exception handlers

---

## 🧪 Phase 8: Testing & Validation

### Step 19: Generate SQL Injection Tests

**📝 Prompt for Copilot Chat:**
```
Generate pytest test cases for database_client.py that verify SQL injection vulnerabilities are fixed:

Test cases should include:
1. Malicious email input: ' OR '1'='1
2. Malicious order_status: '; DROP TABLE Orders; --
3. UNION-based injection attempts
4. Validate that these return errors, not data

Create file: python-services/checkout-service/tests/test_database_security.py
```

<details>
<summary>✅ Expected Test File</summary>

```python
import pytest
from app.client.database_client import DatabaseClient

class TestDatabaseSecurity:
    
    def test_sql_injection_in_customer_search_blocked(self):
        """Verify SQL injection via email parameter is blocked."""
        client = DatabaseClient("test_connection_string")
        
        # Malicious input that would return all records in vulnerable code
        malicious_email = "' OR '1'='1"
        
        # Should return empty list or error, not all orders
        results = client.search_orders_by_customer(malicious_email)
        assert len(results) == 0, "SQL injection returned data!"
    
    def test_sql_injection_table_drop_blocked(self):
        """Verify DROP TABLE injection is blocked."""
        client = DatabaseClient("test_connection_string")
        
        # Attempt to drop table via injection
        malicious_email = "'; DROP TABLE Orders; --"
        
        # Should handle safely without executing DROP
        client.search_orders_by_customer(malicious_email)
        
        # Table should still exist (verify in separate query)
        # This test requires actual DB connection to validate
    
    def test_order_status_validation(self):
        """Verify only valid order statuses are accepted."""
        client = DatabaseClient("test_connection_string")
        
        # Invalid status should raise ValueError
        with pytest.raises(ValueError, match="Invalid order_status"):
            client.create_order(
                customer_id=1,
                total_amount=100.0,
                discount_amount=10.0,
                order_status="'; DROP TABLE Orders; --"
            )
```

</details>

---

### Step 20: Generate NULL Handling Tests

**📝 Prompt for Copilot Chat:**
```
Generate pytest test cases that verify NULL handling is fixed:

Test cases:
1. get_customer_discount with non-existent customer returns 0.0 (not None)
2. get_customer_discount with customer who has no discount returns 0.0
3. create_order with NULL discount_amount handles correctly

Add to test_database_security.py
```

---

### Step 21: Run the Full Test Suite

```bash
cd python-services/checkout-service
pytest tests/test_database_security.py -v
```

**✅ Checkpoint:** All tests should pass

---

## 📊 Phase 9: Verification & Deployment

### Step 22: Create Database Migration Script

**📝 Prompt for Copilot Chat:**
```
Create a complete SQL migration script that applies all database fixes in the correct order:

1. Drop and recreate stored procedures (with fixes)
2. Add missing indexes
3. Clean up orphaned data
4. Add foreign key constraints
5. Add CHECK constraints
6. Fix data types

Save to: database/migrations/001_security_and_performance_fixes.sql
```

---

### Step 23: Generate Deployment Checklist

**📝 Prompt for Copilot Chat:**
```
Create a deployment checklist for these database fixes:

Include:
- Pre-deployment validations
- Backup steps
- Migration execution order
- Rollback plan
- Post-deployment verification tests
- Monitoring alerts to watch

Save to: database/DEPLOYMENT_CHECKLIST.md
```

---

### Step 24: Run the Fixed Code

```bash
# Deploy schema changes (in test environment)
sqlcmd -S localhost -d ShopSphere -i database/migrations/001_security_and_performance_fixes.sql

# Run the checkout service
cd python-services/checkout-service
python demo.py
```

**✅ Expected Results:**
- ✅ Checkout failure rate: 0% (down from 68%)
- ✅ No SQL injection vulnerabilities
- ✅ No NULL handling errors
- ✅ Query execution time: <50ms (down from 3,847ms)
- ✅ All data integrity constraints enforced

---

## 🎯 Final Checkpoint

Run this comprehensive validation:

**📝 Prompt for Copilot Chat:**
```
@workspace Verify all database bugs have been fixed:

Check:
1. ✅ SQL injection vulnerabilities removed (schema.sql + database_client.py)
2. ✅ NULL handling fixed (returns 0 instead of None)
3. ✅ Indexes created (query performance < 100ms)
4. ✅ Foreign key constraints added
5. ✅ CHECK constraints added
6. ✅ Transaction commits added
7. ✅ TLS/SSL enabled
8. ✅ Credentials not logged
9. ✅ Exception logging includes exc_info=True
10. ✅ Input validation on all user inputs

Create a summary report showing before/after for each category.
```

---

## 🏆 Achievement Unlocked

You have successfully:
- ✅ Fixed **2 critical SQL injection vulnerabilities**
- ✅ Fixed **NULL handling bug** affecting 68% of checkouts
- ✅ Created **6 performance-critical indexes**
- ✅ Added **3 data integrity constraints**
- ✅ Implemented **transaction handling** to prevent race conditions
- ✅ Applied **security hardening** (TLS, credential protection)
- ✅ Fixed **36 total bugs** across schema and application code

**Revenue Impact:** $18,000/minute losses stopped ✅  
**Security Impact:** Critical vulnerabilities eliminated ✅  
**Performance Impact:** 77x query speedup (3,847ms → 50ms) ✅

---

## 📚 Key Takeaways

1. **SQL Injection:** Always use parameterized queries, never string concatenation
2. **NULL Handling:** Validate at every layer (database, application, API)
3. **Performance:** Indexes are critical for production scale
4. **Data Integrity:** Foreign keys and CHECK constraints prevent corruption
5. **Transactions:** Always commit changes and handle rollback
6. **Security:** TLS encryption, credential protection, input validation
7. **Logging:** Include exc_info=True for debugging production issues

---

## 🔗 Next Steps

- **Exercise D2:** Monitor database performance with Application Insights
- **Exercise D3:** Implement database connection pooling and retry logic
- **Exercise D4:** Create automated security scanning for SQL injection

---

## 📖 Additional Resources

- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [Microsoft SQL Server Index Design Guidelines](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide)
- [Database Transaction Isolation Levels](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql)
- [Python pyodbc Best Practices](https://github.com/mkleehammer/pyodbc/wiki/Best-Practices)

---

**Workshop Feedback:** How long did this exercise take? Which bugs were hardest to find?
Share your experience in the workshop retrospective!

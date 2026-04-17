-- ============================================================================
-- ShopSphere Database Schema - MS SQL Server
-- ============================================================================
-- This schema contains INTENTIONAL BUGS for the debugging workshop
-- DO NOT use in production without fixing the vulnerabilities
-- ============================================================================

USE [ShopSphere];
GO

-- ============================================================================
-- Table: Customers
-- Stores customer information and loyalty tier
-- ============================================================================
CREATE TABLE Customers (
    CustomerId INT PRIMARY KEY IDENTITY(1,1),
    Email NVARCHAR(255) NOT NULL UNIQUE,
    FirstName NVARCHAR(50),
    LastName NVARCHAR(50),
    LoyaltyPoints INT DEFAULT 0,
    -- BUG 1: LoyaltyTier should have a CHECK constraint
    -- Currently accepts any string, including invalid tiers
    -- Should be: CHECK (LoyaltyTier IN ('Bronze', 'Silver', 'Gold', 'Platinum'))
    LoyaltyTier NVARCHAR(20) DEFAULT 'Bronze',
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    LastPurchaseDate DATETIME2
);

-- ============================================================================
-- Table: DiscountRules
-- Defines discount rules for different customer segments
-- ============================================================================
CREATE TABLE DiscountRules (
    RuleId INT PRIMARY KEY IDENTITY(1,1),
    RuleName NVARCHAR(100) NOT NULL,
    LoyaltyTier NVARCHAR(20),
    MinPurchaseAmount DECIMAL(10,2),
    -- BUG 2: DiscountPercentage stored as DECIMAL(3,2) 
    -- This limits max value to 9.99 (not 100.00)
    -- Should be DECIMAL(5,2) to support values up to 100.00
    DiscountPercentage DECIMAL(3,2),
    DiscountFixedAmount DECIMAL(10,2),
    IsActive BIT DEFAULT 1,
    ValidFrom DATETIME2,
    ValidUntil DATETIME2
);

-- ============================================================================
-- Table: Orders
-- Stores order header information
-- ============================================================================
CREATE TABLE Orders (
    OrderId INT PRIMARY KEY IDENTITY(1,1),
    CustomerId INT NOT NULL,
    -- BUG 3: Missing foreign key constraint to Customers table
    -- This allows orphaned orders with invalid CustomerId values
    -- Should have: FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId)
    OrderDate DATETIME2 DEFAULT GETUTCDATE(),
    TotalAmount DECIMAL(10,2) NOT NULL,
    DiscountAmount DECIMAL(10,2) DEFAULT 0,
    FinalAmount DECIMAL(10,2) NOT NULL,
    OrderStatus NVARCHAR(20) DEFAULT 'Pending',
    PaymentStatus NVARCHAR(20) DEFAULT 'Pending'
);

-- ============================================================================
-- Table: OrderItems
-- Stores individual line items for each order
-- ============================================================================
CREATE TABLE OrderItems (
    OrderItemId INT PRIMARY KEY IDENTITY(1,1),
    OrderId INT NOT NULL,
    ProductId INT NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    LineTotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (OrderId) REFERENCES Orders(OrderId)
    -- BUG 4: Missing index on OrderId
    -- Queries joining Orders with OrderItems will be slow
    -- Should have: CREATE INDEX IX_OrderItems_OrderId ON OrderItems(OrderId)
);

-- ============================================================================
-- Table: PaymentAuditLog
-- Audit trail for all payment attempts
-- ============================================================================
CREATE TABLE PaymentAuditLog (
    AuditId INT PRIMARY KEY IDENTITY(1,1),
    OrderId INT NOT NULL,
    PaymentAttemptDate DATETIME2 DEFAULT GETUTCDATE(),
    PaymentAmount DECIMAL(10,2),
    PaymentMethod NVARCHAR(50),
    TransactionId NVARCHAR(100),
    Status NVARCHAR(20),
    ErrorMessage NVARCHAR(MAX),
    -- BUG 5: No index on OrderId or TransactionId
    -- Audit queries for specific orders will perform table scans
    ProcessingTimeMs INT
);

-- ============================================================================
-- Insert Sample Data
-- ============================================================================

INSERT INTO Customers (Email, FirstName, LastName, LoyaltyPoints, LoyaltyTier, LastPurchaseDate)
VALUES 
    ('john.doe@example.com', 'John', 'Doe', 150, 'Bronze', '2026-04-01'),
    ('jane.smith@example.com', 'Jane', 'Smith', 520, 'Silver', '2026-04-05'),
    ('bob.wilson@example.com', 'Bob', 'Wilson', 1250, 'Gold', '2026-04-08'),
    ('alice.brown@example.com', 'Alice', 'Brown', 3500, 'Platinum', '2026-04-09'),
    -- BUG 1 EXAMPLE: Invalid tier inserted successfully
    ('hacker@evil.com', 'Bad', 'Actor', 0, 'SuperAdmin', '2026-04-10');

INSERT INTO DiscountRules (RuleName, LoyaltyTier, MinPurchaseAmount, DiscountPercentage, DiscountFixedAmount, IsActive, ValidFrom, ValidUntil)
VALUES
    ('Bronze Welcome', 'Bronze', 50.00, 5.00, NULL, 1, '2026-01-01', '2026-12-31'),
    ('Silver Standard', 'Silver', 100.00, 10.00, NULL, 1, '2026-01-01', '2026-12-31'),
    ('Gold Premium', 'Gold', 150.00, 15.00, NULL, 1, '2026-01-01', '2026-12-31'),
    -- BUG 2 EXAMPLE: This insert will fail or truncate - 25% cannot fit in DECIMAL(3,2)
    -- ('Platinum Elite', 'Platinum', 200.00, 25.00, NULL, 1, '2026-01-01', '2026-12-31'),
    ('Fixed $20 Off', NULL, 100.00, NULL, 20.00, 1, '2026-01-01', '2026-12-31');

-- BUG 3 EXAMPLE: Orphaned order (CustomerId 999 doesn't exist)
INSERT INTO Orders (CustomerId, TotalAmount, DiscountAmount, FinalAmount, OrderStatus, PaymentStatus)
VALUES (999, 100.00, 0.00, 100.00, 'Processing', 'Pending');

GO

-- ============================================================================
-- Stored Procedure: sp_GetCustomerDiscount
-- Calculates discount for a customer based on loyalty tier and amount
-- ============================================================================
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
    
    -- BUG 6: No NULL check for @LoyaltyTier
    -- If CustomerId doesn't exist, @LoyaltyTier is NULL
    -- The subsequent query will return no rows and @DiscountAmount stays NULL
    -- This causes the same NoneType error in Python as the original bug
    
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
        -- BUG 7: Should set @DiscountAmount = 0 here
        -- Instead leaves it NULL, propagating the bug to application layer
        SET @DiscountAmount = NULL;
END;
GO

-- ============================================================================
-- Stored Procedure: sp_CreateOrder (VULNERABLE - SQL Injection)
-- Creates a new order and returns the OrderId
-- ============================================================================
CREATE PROCEDURE sp_CreateOrder
    @CustomerId INT,
    @TotalAmount DECIMAL(10,2),
    @DiscountAmount DECIMAL(10,2),
    @OrderStatus NVARCHAR(20),
    @OrderId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- BUG 8: Uses dynamic SQL with string concatenation
    -- This is vulnerable to SQL injection if @OrderStatus comes from user input
    -- Should use parameterized queries instead
    DECLARE @SQL NVARCHAR(MAX);
    SET @SQL = 'INSERT INTO Orders (CustomerId, TotalAmount, DiscountAmount, FinalAmount, OrderStatus, PaymentStatus) 
                VALUES (' + CAST(@CustomerId AS NVARCHAR) + ', ' 
                + CAST(@TotalAmount AS NVARCHAR) + ', ' 
                + CAST(@DiscountAmount AS NVARCHAR) + ', ' 
                + CAST(@TotalAmount - @DiscountAmount AS NVARCHAR) + ', ''' 
                + @OrderStatus + ''', ''Pending'')';
    
    EXEC sp_executesql @SQL;
    SET @OrderId = SCOPE_IDENTITY();
END;
GO

-- ============================================================================
-- Stored Procedure: sp_ProcessPayment
-- Records payment attempt and updates order status
-- ============================================================================
CREATE PROCEDURE sp_ProcessPayment
    @OrderId INT,
    @PaymentAmount DECIMAL(10,2),
    @PaymentMethod NVARCHAR(50),
    @TransactionId NVARCHAR(100),
    @Success BIT
AS
BEGIN
    -- BUG 9: Missing transaction isolation level
    -- Without BEGIN TRANSACTION, concurrent calls can cause race conditions
    -- Two payments could be processed for the same order
    SET NOCOUNT ON;
    
    DECLARE @StartTime DATETIME2 = GETUTCDATE();
    
    -- Log the payment attempt
    INSERT INTO PaymentAuditLog (OrderId, PaymentAmount, PaymentMethod, TransactionId, Status, ProcessingTimeMs)
    VALUES (@OrderId, @PaymentAmount, @PaymentMethod, @TransactionId, 
            CASE WHEN @Success = 1 THEN 'Success' ELSE 'Failed' END,
            DATEDIFF(MILLISECOND, @StartTime, GETUTCDATE()));
    
    -- Update order if payment succeeded
    IF @Success = 1
    BEGIN
        UPDATE Orders
        SET PaymentStatus = 'Completed',
            OrderStatus = 'Confirmed'
        WHERE OrderId = @OrderId;
    END
    -- BUG 10: No ELSE clause to handle failed payments
    -- Failed payments are logged but order status isn't updated
    -- Orders remain in 'Pending' state forever
END;
GO

-- ============================================================================
-- View: vw_CustomerOrderHistory
-- Shows order history with customer details
-- ============================================================================
CREATE VIEW vw_CustomerOrderHistory
AS
SELECT 
    o.OrderId,
    o.OrderDate,
    c.CustomerId,
    c.Email,
    c.FirstName + ' ' + c.LastName AS CustomerName,
    c.LoyaltyTier,
    o.TotalAmount,
    o.DiscountAmount,
    o.FinalAmount,
    o.OrderStatus,
    o.PaymentStatus,
    -- BUG 11: Using COUNT without checking for NULL OrderItems
    -- Orders without items will still show ItemCount = 0 (misleading)
    (SELECT COUNT(*) FROM OrderItems oi WHERE oi.OrderId = o.OrderId) AS ItemCount
FROM Orders o
LEFT JOIN Customers c ON o.CustomerId = c.CustomerId;
-- BUG 12: LEFT JOIN allows orphaned orders to appear in view
-- Should use INNER JOIN to exclude orders with invalid CustomerId
GO

-- ============================================================================
-- Function: fn_CalculateLoyaltyPoints (Contains Logic Bug)
-- Returns loyalty points earned for a purchase amount
-- ============================================================================
CREATE FUNCTION fn_CalculateLoyaltyPoints
(
    @PurchaseAmount DECIMAL(10,2),
    @LoyaltyTier NVARCHAR(20)
)
RETURNS INT
AS
BEGIN
    DECLARE @Points INT;
    
    -- BUG 13: Logic error - uses >= instead of = for tier comparison
    -- A Gold customer gets Bronze points (1x) + Silver points (2x) + Gold points (3x) = 6x
    -- This is incorrect but appears to be a "bonus" so might go unnoticed
    IF @LoyaltyTier >= 'Platinum'
        SET @Points = CAST(@PurchaseAmount * 5 AS INT);
    IF @LoyaltyTier >= 'Gold'
        SET @Points = CAST(@PurchaseAmount * 3 AS INT);
    IF @LoyaltyTier >= 'Silver'
        SET @Points = CAST(@PurchaseAmount * 2 AS INT);
    IF @LoyaltyTier >= 'Bronze'
        SET @Points = CAST(@PurchaseAmount * 1 AS INT);
    ELSE
        SET @Points = 0;
    
    RETURN @Points;
END;
GO

-- ============================================================================
-- Index: Create missing indexes for common queries (COMMENTED OUT - BUG 4)
-- ============================================================================
-- These indexes are needed but not created, causing performance issues

-- CREATE INDEX IX_Orders_CustomerId ON Orders(CustomerId);
-- CREATE INDEX IX_Orders_OrderDate ON Orders(OrderDate);
-- CREATE INDEX IX_OrderItems_OrderId ON OrderItems(OrderId);
-- CREATE INDEX IX_PaymentAuditLog_OrderId ON PaymentAuditLog(OrderId);
-- CREATE INDEX IX_PaymentAuditLog_TransactionId ON PaymentAuditLog(TransactionId);
-- CREATE INDEX IX_Customers_Email ON Customers(Email); -- Already covered by UNIQUE constraint
-- CREATE INDEX IX_Customers_LoyaltyTier ON Customers(LoyaltyTier);

GO

PRINT 'ShopSphere Database Schema created successfully.';
PRINT 'WARNING: This schema contains INTENTIONAL BUGS for workshop purposes.';
PRINT 'Total bugs embedded: 13';
PRINT 'Categories: Schema design, data integrity, SQL injection, NULL handling, performance, logic errors';

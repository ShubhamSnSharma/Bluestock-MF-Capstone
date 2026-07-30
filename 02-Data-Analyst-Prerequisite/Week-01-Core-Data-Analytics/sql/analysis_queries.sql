-- =====================================================
-- Week 1 - Data Analytics Internship
-- SQL Practice Queries
-- Dataset: Sample Superstore
-- Author: Shubham Sharma
-- =====================================================

-- =====================================================
-- 1. Display all records
-- =====================================================

SELECT *
FROM superstore;


-- =====================================================
-- 2. Display selected columns
-- =====================================================

SELECT `Order ID`, Customer Name, Sales, Profit
FROM superstore;


-- =====================================================
-- 3. Orders with Sales greater than 1000
-- =====================================================

SELECT *
FROM superstore
WHERE Sales > 1000;


-- =====================================================
-- 4. Furniture orders sorted by Profit
-- =====================================================

SELECT *
FROM superstore
WHERE Category = 'Furniture'
ORDER BY Profit DESC;


-- =====================================================
-- 5. Top 10 highest sales transactions
-- =====================================================

SELECT *
FROM superstore
ORDER BY Sales DESC
LIMIT 10;


-- =====================================================
-- 6. Total Sales and Profit
-- =====================================================

SELECT
    SUM(Sales) AS Total_Sales,
    SUM(Profit) AS Total_Profit
FROM superstore;


-- =====================================================
-- 7. Sales by Category
-- =====================================================

SELECT
    Category,
    SUM(Sales) AS Total_Sales
FROM superstore
GROUP BY Category;


-- =====================================================
-- 8. Profit by Region
-- =====================================================

SELECT
    Region,
    SUM(Profit) AS Total_Profit
FROM superstore
GROUP BY Region
ORDER BY Total_Profit DESC;


-- =====================================================
-- 9. Customer Segment Analysis
-- =====================================================

SELECT
    Segment,
    SUM(Sales) AS Total_Sales,
    SUM(Profit) AS Total_Profit
FROM superstore
GROUP BY Segment;


-- =====================================================
-- 10. Categories with Sales greater than 500000
-- =====================================================

SELECT
    Category,
    SUM(Sales) AS Total_Sales
FROM superstore
GROUP BY Category
HAVING SUM(Sales) > 500000;


-- =====================================================
-- 11. Top 10 Customers by Sales
-- =====================================================

SELECT
    `Customer Name`,
    SUM(Sales) AS Total_Sales
FROM superstore
GROUP BY `Customer Name`
ORDER BY Total_Sales DESC
LIMIT 10;


-- =====================================================
-- 12. Top 10 Products by Sales
-- =====================================================

SELECT
    `Product Name`,
    SUM(Sales) AS Total_Sales
FROM superstore
GROUP BY `Product Name`
ORDER BY Total_Sales DESC
LIMIT 10;


-- =====================================================
-- 13. Average Discount by Category
-- =====================================================

SELECT
    Category,
    AVG(Discount) AS Avg_Discount
FROM superstore
GROUP BY Category;


-- =====================================================
-- 14. Monthly Sales Trend
-- =====================================================

SELECT
    YEAR(`Order Date`) AS Year,
    MONTH(`Order Date`) AS Month,
    SUM(Sales) AS Monthly_Sales
FROM superstore
GROUP BY Year, Month
ORDER BY Year, Month;


-- =====================================================
-- 15. Product Performance (Subquery)
-- Products with above-average sales
-- =====================================================

SELECT
    `Product Name`,
    Sales
FROM superstore
WHERE Sales >
(
    SELECT AVG(Sales)
    FROM superstore
);


-- =====================================================
-- 16. Customer Ranking (Window Function)
-- =====================================================

SELECT
    `Customer Name`,
    SUM(Sales) AS Total_Sales,
    RANK() OVER (ORDER BY SUM(Sales) DESC) AS Sales_Rank
FROM superstore
GROUP BY `Customer Name`;


-- =====================================================
-- 17. Running Total of Sales (Window Function)
-- =====================================================

SELECT
    `Order Date`,
    Sales,
    SUM(Sales)
    OVER (
        ORDER BY `Order Date`
    ) AS Running_Total
FROM superstore;


-- =====================================================
-- 18. JOIN Example
-- (Self Join for demonstration)
-- =====================================================

SELECT
    A.`Order ID`,
    A.`Customer Name`,
    B.Region
FROM superstore A
JOIN superstore B
ON A.`Order ID` = B.`Order ID`
LIMIT 10;
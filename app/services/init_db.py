"""
Script to initialize the SQLite database with sample data.
Creates tables for a realistic e-commerce scenario.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random


def create_sample_database(db_path: str = "./data/sample.db"):
    """Create and populate sample database."""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript("""
        -- Customers table
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            city TEXT,
            country TEXT NOT NULL,
            registration_date DATE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            credit_limit REAL DEFAULT 1000.00
        );
        
        -- Products table
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            supplier TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Orders table
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date DATETIME NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            total_amount REAL NOT NULL,
            shipping_address TEXT,
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        
        -- Order Items table
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount REAL DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        
        -- Inventory Logs table
        CREATE TABLE inventory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            change_type TEXT NOT NULL,
            quantity_change INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)
    
    # Sample data
    customers_data = [
        ("John Smith", "john.smith@email.com", "New York", "USA", "2023-01-15", 1, 5000.00),
        ("Emma Wilson", "emma.w@email.com", "London", "UK", "2023-02-20", 1, 3000.00),
        ("Carlos García", "carlos.g@email.com", "Madrid", "Spain", "2023-03-10", 1, 2500.00),
        ("Yuki Tanaka", "yuki.t@email.com", "Tokyo", "Japan", "2023-04-05", 1, 4000.00),
        ("Marie Dubois", "marie.d@email.com", "Paris", "France", "2023-05-12", 1, 3500.00),
        ("Hans Mueller", "hans.m@email.com", "Berlin", "Germany", "2023-06-18", 1, 2800.00),
        ("Priya Patel", "priya.p@email.com", "Mumbai", "India", "2023-07-22", 1, 2000.00),
        ("Lucas Santos", "lucas.s@email.com", "São Paulo", "Brazil", "2023-08-30", 0, 1500.00),
        ("Sofia Rossi", "sofia.r@email.com", "Rome", "Italy", "2023-09-14", 1, 3200.00),
        ("Ahmed Hassan", "ahmed.h@email.com", "Cairo", "Egypt", "2023-10-08", 1, 1800.00),
        ("Anna Kowalski", "anna.k@email.com", "Warsaw", "Poland", "2023-11-25", 1, 2200.00),
        ("Chen Wei", "chen.w@email.com", "Shanghai", "China", "2023-12-03", 1, 4500.00),
        ("Olivia Brown", "olivia.b@email.com", "Sydney", "Australia", "2024-01-10", 1, 3800.00),
        ("Mohammed Ali", "mo.ali@email.com", "Dubai", "UAE", "2024-02-14", 1, 6000.00),
        ("Emily Davis", "emily.d@email.com", "Toronto", "Canada", "2024-03-20", 1, 2900.00),
    ]
    
    cursor.executemany("""
        INSERT INTO customers (name, email, city, country, registration_date, is_active, credit_limit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, customers_data)
    
    products_data = [
        ("Laptop Pro 15", "Electronics", 1299.99, 50, "TechCorp"),
        ("Wireless Mouse", "Electronics", 29.99, 200, "TechCorp"),
        ("USB-C Hub", "Electronics", 49.99, 150, "ConnectPlus"),
        ("Mechanical Keyboard", "Electronics", 89.99, 100, "KeyMaster"),
        ("Monitor 27inch", "Electronics", 349.99, 30, "DisplayTech"),
        ("Desk Chair Ergo", "Furniture", 299.99, 40, "ComfortCo"),
        ("Standing Desk", "Furniture", 599.99, 25, "ComfortCo"),
        ("Desk Lamp LED", "Furniture", 39.99, 80, "LightUp"),
        ("Notebook Set", "Office", 12.99, 500, "PaperWorld"),
        ("Pen Pack Premium", "Office", 8.99, 300, "PaperWorld"),
        ("Webcam HD", "Electronics", 79.99, 120, "TechCorp"),
        ("Headphones Noise-Cancel", "Electronics", 199.99, 60, "AudioPro"),
        ("Phone Stand", "Accessories", 19.99, 250, "HoldIt"),
        ("Cable Organizer", "Accessories", 14.99, 180, "HoldIt"),
        ("Portable Charger", "Electronics", 44.99, 200, "PowerUp"),
    ]
    
    cursor.executemany("""
        INSERT INTO products (name, category, price, stock_quantity, supplier)
        VALUES (?, ?, ?, ?, ?)
    """, products_data)
    
    # Generate realistic orders
    statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    base_date = datetime(2024, 1, 1)
    
    orders_data = []
    order_items_data = []
    order_id = 1
    
    for i in range(100):  # 100 orders
        customer_id = random.randint(1, 15)
        order_date = base_date + timedelta(days=random.randint(0, 300), hours=random.randint(0, 23))
        status = random.choices(statuses, weights=[5, 10, 15, 65, 5])[0]
        
        # Generate order items
        num_items = random.randint(1, 5)
        total = 0
        
        for j in range(num_items):
            product_id = random.randint(1, 15)
            quantity = random.randint(1, 3)
            # Get product price (simplified - in real app would query)
            unit_price = products_data[product_id - 1][2]
            discount = random.choice([0, 0, 0, 5, 10, 15])
            item_total = quantity * unit_price * (1 - discount/100)
            total += item_total
            order_items_data.append((order_id, product_id, quantity, unit_price, discount))
        
        orders_data.append((
            customer_id,
            order_date.strftime("%Y-%m-%d %H:%M:%S"),
            status,
            round(total, 2),
            f"Address {i+1}, City",
            None if random.random() > 0.2 else "Rush delivery requested"
        ))
        order_id += 1
    
    cursor.executemany("""
        INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, orders_data)
    
    cursor.executemany("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount)
        VALUES (?, ?, ?, ?, ?)
    """, order_items_data)
    
    # Generate inventory logs
    inventory_logs = []
    for product_id in range(1, 16):
        for _ in range(random.randint(3, 8)):
            change_type = random.choice(["restock", "sale", "adjustment", "return"])
            if change_type == "restock":
                qty = random.randint(10, 50)
            elif change_type == "sale":
                qty = -random.randint(1, 5)
            elif change_type == "return":
                qty = random.randint(1, 3)
            else:
                qty = random.randint(-5, 5)
            
            log_date = base_date + timedelta(days=random.randint(0, 300))
            reasons = {
                "restock": "Supplier delivery",
                "sale": "Customer purchase",
                "adjustment": "Inventory count correction",
                "return": "Customer return - item defective"
            }
            inventory_logs.append((
                product_id,
                change_type,
                qty,
                log_date.strftime("%Y-%m-%d %H:%M:%S"),
                reasons[change_type]
            ))
    
    cursor.executemany("""
        INSERT INTO inventory_logs (product_id, change_type, quantity_change, timestamp, reason)
        VALUES (?, ?, ?, ?, ?)
    """, inventory_logs)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Sample database created at: {db_path}")
    print("   Tables: customers, products, orders, order_items, inventory_logs")
    print(f"   - 15 customers")
    print(f"   - 15 products")
    print(f"   - 100 orders")
    print(f"   - {len(order_items_data)} order items")
    print(f"   - {len(inventory_logs)} inventory logs")


if __name__ == "__main__":
    create_sample_database()

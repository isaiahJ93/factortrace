#!/usr/bin/env python3
import sqlite3
from datetime import datetime

# Connect to SQLite database
conn = sqlite3.connect('factortrace.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='emission_factors';
""")

if cursor.fetchone():
    print("Table exists, adding sample emission factors...")
    
    # Add some sample emission factors
    factors = [
        # Business Travel
        ("Flight - Domestic", "business_travel", 3, 0.246, "km", "DEFRA 2024", "Domestic flights average"),
        ("Flight - Short Haul", "business_travel", 3, 0.151, "km", "DEFRA 2024", "Flights <3,700km"),
        ("Flight - Long Haul", "business_travel", 3, 0.147, "km", "DEFRA 2024", "Flights >3,700km"),
        
        # Electricity
        ("US Grid Average", "electricity", 2, 0.385, "kWh", "EPA eGRID 2024", "US national average"),
        ("UK Grid", "electricity", 2, 0.233, "kWh", "DEFRA 2024", "UK grid average"),
    ]
    
    for factor in factors:
        cursor.execute("""
            INSERT OR REPLACE INTO emission_factors 
            (name, category, scope, factor, unit, source, description, is_active, valid_from)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (*factor, datetime.now().isoformat()))
    
    conn.commit()
    print(f"Added {len(factors)} emission factors")
else:
    print("Table 'emission_factors' not found!")

# Check what we have
cursor.execute("SELECT COUNT(*) FROM emission_factors")
count = cursor.fetchone()[0]
print(f"Total emission factors in database: {count}")

conn.close()

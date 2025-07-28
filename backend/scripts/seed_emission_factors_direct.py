# backend/scripts/seed_emission_factors_direct.py
"""
Direct SQL seeding to avoid import issues
"""
import sqlite3
from datetime import datetime

# Sample emission factors to get you started
SAMPLE_FACTORS = [
    # Scope 1 - Stationary Combustion
    ("Natural Gas", "stationary_combustion", 1, 0.185, "kWh", "EPA 2024"),
    ("Propane", "stationary_combustion", 1, 1.51, "liter", "EPA 2024"),
    ("Diesel", "stationary_combustion", 1, 2.68, "liter", "DEFRA 2024"),
    ("Gasoline", "stationary_combustion", 1, 2.31, "liter", "EPA 2024"),
    
    # Scope 1 - Mobile Combustion
    ("Car Small Petrol", "mobile_combustion", 1, 0.14, "km", "DEFRA 2024"),
    ("Car Medium Diesel", "mobile_combustion", 1, 0.16, "km", "DEFRA 2024"),
    ("Car Electric", "mobile_combustion", 1, 0.053, "km", "DEFRA 2024"),
    
    # Scope 2 - Electricity
    ("Grid US Average", "electricity", 2, 0.385, "kWh", "EPA eGRID 2024"),
    ("Grid UK", "electricity", 2, 0.233, "kWh", "DEFRA 2024"),
    ("Grid California", "electricity", 2, 0.203, "kWh", "CARB 2024"),
    ("Renewable Solar", "electricity", 2, 0.041, "kWh", "IPCC 2024"),
    ("Renewable Wind", "electricity", 2, 0.011, "kWh", "IPCC 2024"),
    
    # Scope 3 - Business Travel
    ("Flight Domestic", "business_travel", 3, 0.246, "km", "DEFRA 2024"),
    ("Flight International", "business_travel", 3, 0.183, "km", "DEFRA 2024"),
    ("Train", "business_travel", 3, 0.037, "km", "DEFRA 2024"),
    ("Hotel Stay", "business_travel", 3, 10.3, "night", "Cornell 2024"),
    
    # Scope 3 - Employee Commuting
    ("Car Average", "employee_commuting", 3, 0.171, "km", "EPA 2024"),
    ("Bus", "employee_commuting", 3, 0.089, "km", "DEFRA 2024"),
    ("Subway", "employee_commuting", 3, 0.028, "km", "DEFRA 2024"),
    
    # Scope 3 - Waste
    ("Landfill Mixed", "waste", 3, 0.467, "kg", "EPA WARM 2024"),
    ("Recycling Mixed", "waste", 3, -0.821, "kg", "EPA WARM 2024"),
]

def seed_directly():
    # Connect to SQLite database
    conn = sqlite3.connect('factortrace.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emission_factors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(100) NOT NULL,
        scope INTEGER NOT NULL,
        factor FLOAT NOT NULL,
        unit VARCHAR(50) NOT NULL,
        source VARCHAR(255),
        description TEXT,
        is_active BOOLEAN DEFAULT 1,
        valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        valid_to TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_factor_category_scope ON emission_factors(category, scope)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_factor_active ON emission_factors(is_active)')
    
    # Check if table has data
    cursor.execute('SELECT COUNT(*) FROM emission_factors')
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"Found {count} existing emission factors")
        response = input("Clear and reseed? (y/N): ")
        if response.lower() == 'y':
            cursor.execute('DELETE FROM emission_factors')
            conn.commit()
        else:
            print("Keeping existing data")
            conn.close()
            return
    
    # Insert sample factors
    now = datetime.utcnow().isoformat()
    for name, category, scope, factor, unit, source in SAMPLE_FACTORS:
        description = f"{name} - {category} (scope_{scope})"
        cursor.execute('''
        INSERT INTO emission_factors 
        (name, category, scope, factor, unit, source, description, is_active, valid_from, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        ''', (name, category, scope, factor, unit, source, description, now, now, now))
    
    conn.commit()
    print(f"✅ Seeded {len(SAMPLE_FACTORS)} emission factors")
    
    # Verify
    cursor.execute('SELECT scope, COUNT(*) FROM emission_factors GROUP BY scope')
    for scope, count in cursor.fetchall():
        print(f"  Scope {scope}: {count} factors")
    
    conn.close()

if __name__ == "__main__":
    print("🌱 Direct seeding emission factors...")
    seed_directly()
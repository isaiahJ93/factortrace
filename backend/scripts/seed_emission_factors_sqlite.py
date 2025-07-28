import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
from decimal import Decimal

# Your EMISSION_FACTORS dictionary here...

def seed_emission_factors():
    """Seed SQLite database with emission factors"""
    conn = sqlite3.connect('factortrace.db')
    cursor = conn.cursor()
    
    # Clear existing factors
    cursor.execute("DELETE FROM emission_factors")
    
    count = 0
    for scope, categories in EMISSION_FACTORS.items():
        scope_num = int(scope.split('_')[1])
        
        for category, factors_list in categories.items():
            for factor_data in factors_list:
                cursor.execute("""
                    INSERT INTO emission_factors (
                        name, category, scope, factor, unit, source, 
                        description, is_active, valid_from
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    factor_data['name'],
                    category,
                    scope_num,
                    factor_data['factor'],
                    factor_data['unit'],
                    factor_data.get('source', 'Unknown'),
                    factor_data.get('description', ''),
                    datetime.utcnow().isoformat()
                ))
                count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Successfully seeded {count} emission factors")

if __name__ == "__main__":
    seed_emission_factors()

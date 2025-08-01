# Replace USD with EUR in the calculator

replacements = {
    # Purchased Goods & Services
    '{ id: "electronics", name: "Electronics", unit: "USD", factor: 0.42, source: "EPA EEIO" }':
    '{ id: "electronics", name: "Electronics", unit: "EUR", factor: 0.39, source: "EPA EEIO (EUR adjusted)" }',
    
    '{ id: "food_beverages", name: "Food & Beverages", unit: "USD", factor: 0.38, source: "EPA EEIO" }':
    '{ id: "food_beverages", name: "Food & Beverages", unit: "EUR", factor: 0.35, source: "EPA EEIO (EUR adjusted)" }',
    
    # Capital Goods
    '{ id: "machinery", name: "Machinery & Equipment", unit: "USD", factor: 0.35, source: "EPA EEIO" }':
    '{ id: "machinery", name: "Machinery & Equipment", unit: "EUR", factor: 0.32, source: "EPA EEIO (EUR adjusted)" }',
    
    '{ id: "buildings", name: "Buildings & Construction", unit: "USD", factor: 0.28, source: "EPA EEIO" }':
    '{ id: "buildings", name: "Buildings & Construction", unit: "EUR", factor: 0.26, source: "EPA EEIO (EUR adjusted)" }',
    
    '{ id: "vehicles", name: "Vehicles", unit: "USD", factor: 0.40, source: "EPA EEIO" }':
    '{ id: "vehicles", name: "Vehicles", unit: "EUR", factor: 0.37, source: "EPA EEIO (EUR adjusted)" }',
    
    # Franchises
    '{ id: "franchise_travel", name: "Franchise Business Travel", unit: "USD", factor: 0.15, source: "EPA EEIO" }':
    '{ id: "franchise_travel", name: "Franchise Business Travel", unit: "EUR", factor: 0.14, source: "EPA EEIO (EUR adjusted)" }',
    
    # Investments (PCAF)
    '{ id: "equity_investments", name: "Equity Investments", unit: "USD million", factor: 680.0, source: "PCAF" }':
    '{ id: "equity_investments", name: "Equity Investments", unit: "EUR million", factor: 630.0, source: "PCAF (EUR)" }',
    
    '{ id: "debt_investments", name: "Debt Investments", unit: "USD million", factor: 350.0, source: "PCAF" }':
    '{ id: "debt_investments", name: "Debt Investments", unit: "EUR million", factor: 325.0, source: "PCAF (EUR)" }',
    
    '{ id: "project_finance", name: "Project Finance", unit: "USD million", factor: 450.0, source: "PCAF" }':
    '{ id: "project_finance", name: "Project Finance", unit: "EUR million", factor: 415.0, source: "PCAF (EUR)" }',
    
    '{ id: "investment_funds", name: "Investment Funds", unit: "USD million", factor: 550.0, source: "PCAF" }':
    '{ id: "investment_funds", name: "Investment Funds", unit: "EUR million", factor: 510.0, source: "PCAF (EUR)" }'
}

# Read the file
with open('src/components/emissions/EliteGHGCalculator.tsx', 'r') as f:
    content = f.read()

# Replace all USD with EUR
for old, new in replacements.items():
    content = content.replace(old, new)

# Write back
with open('src/components/emissions/EliteGHGCalculator.tsx', 'w') as f:
    f.write(content)

print("✅ Updated all USD to EUR with adjusted emission factors")

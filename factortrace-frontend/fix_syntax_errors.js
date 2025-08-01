const fs = require('fs');

const filePath = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Fix missing commas in the emission factors array
const fixes = [
  { find: '{ id: "product_incineration", name: "Products Incinerated", unit: "tonnes", factor: 21.0, source: "DEFRA 2023" }\n          { id: "product_landfill"', 
    replace: '{ id: "product_incineration", name: "Products Incinerated", unit: "tonnes", factor: 21.0, source: "DEFRA 2023" },\n          { id: "product_landfill"' },
  
  { find: '{ id: "product_lifetime_energy", name: "Product Lifetime Energy", unit: "units", factor: 150.0, source: "LCA estimate" }\n          { id: "product_recycling"',
    replace: '{ id: "product_lifetime_energy", name: "Product Lifetime Energy", unit: "units", factor: 150.0, source: "LCA estimate" },\n          { id: "product_recycling"' },
  
  { find: '{ id: "sf6_leakage", name: "SF6 Leakage", unit: "kg", factor: 22800.0, source: "IPCC AR5" }\n          { id: "steel_products"',
    replace: '{ id: "sf6_leakage", name: "SF6 Leakage", unit: "kg", factor: 22800.0, source: "IPCC AR5" },\n          { id: "steel_products"' },
  
  { find: '{ id: "third_party_logistics", name: "3PL Distribution", unit: "tonne.km", factor: 0.096, source: "DEFRA 2023" }\n          { id: "transmission_losses"',
    replace: '{ id: "third_party_logistics", name: "3PL Distribution", unit: "tonne.km", factor: 0.096, source: "DEFRA 2023" },\n          { id: "transmission_losses"' },
  
  { find: '{ id: "transmission_losses", name: "T&D Losses", unit: "kWh", factor: 0.020, source: "DEFRA 2023" }\n          { id: "upstream_electricity"',
    replace: '{ id: "transmission_losses", name: "T&D Losses", unit: "kWh", factor: 0.020, source: "DEFRA 2023" },\n          { id: "upstream_electricity"' },
  
  { find: '{ id: "vehicles", name: "Vehicles", unit: "EUR", factor: 0.37, source: "EPA EEIO (EUR adjusted)" }\n          { id: "waste_composted"',
    replace: '{ id: "vehicles", name: "Vehicles", unit: "EUR", factor: 0.37, source: "EPA EEIO (EUR adjusted)" },\n          { id: "waste_composted"' },
];

// Apply all fixes
fixes.forEach(fix => {
  content = content.replace(fix.find, fix.replace);
});

// Also fix any other patterns of missing commas between objects
content = content.replace(/}\s*\n\s*{(?= id:)/g, '},\n          {');

fs.writeFileSync(filePath, content);
console.log('✅ Fixed syntax errors in EliteGHGCalculator.tsx');

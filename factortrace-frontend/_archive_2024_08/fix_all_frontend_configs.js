const fs = require('fs');

// All potential configs that might be needed
const ALL_CONFIGS = `
// Emission calculation constants
const EMISSION_FACTORS = {
  electricity: 0.233, // kg CO2e/kWh
  natural_gas: 0.185, // kg CO2e/kWh
  diesel: 2.687, // kg CO2e/liter
  petrol: 2.392, // kg CO2e/liter
  waste: 0.467, // kg CO2e/kg
};

const SCOPE3_CATEGORIES = {
  "1": "Purchased goods and services",
  "2": "Capital goods",
  "3": "Fuel-and-energy-related activities",
  "4": "Upstream transportation and distribution",
  "5": "Waste generated in operations",
  "6": "Business travel",
  "7": "Employee commuting",
  "8": "Upstream leased assets",
  "9": "Downstream transportation and distribution",
  "10": "Processing of sold products",
  "11": "Use of sold products",
  "12": "End-of-life treatment of sold products",
  "13": "Downstream leased assets",
  "14": "Franchises",
  "15": "Investments"
};

const EMISSION_SOURCES = {
  ELECTRICITY: 'electricity',
  NATURAL_GAS: 'natural_gas',
  FLEET: 'fleet',
  WASTE: 'waste',
  TRAVEL: 'travel',
  COMMUTING: 'commuting',
  SUPPLY_CHAIN: 'supply_chain'
};

const REPORT_TYPES = {
  ESRS_E1: 'ESRS E1 - Climate Change',
  GRI_305: 'GRI 305 - Emissions',
  CDP: 'CDP Climate Change',
  TCFD: 'TCFD Report'
};

const UNITS = {
  ENERGY: 'kWh',
  MASS: 'kg',
  DISTANCE: 'km',
  CURRENCY: 'EUR',
  EMISSIONS: 'tCO2e'
};

const DEFAULT_VALUES = {
  REPORTING_YEAR: new Date().getFullYear().toString(),
  CURRENCY: 'EUR',
  LANGUAGE: 'en',
  COUNTRY: 'US'
};
`;

// Read the file
const filePath = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Check which constants are already defined
const missingConfigs = [];
if (!content.includes('const EMISSION_FACTORS')) missingConfigs.push('EMISSION_FACTORS');
if (!content.includes('const EMISSION_SOURCES')) missingConfigs.push('EMISSION_SOURCES');
if (!content.includes('const REPORT_TYPES')) missingConfigs.push('REPORT_TYPES');
if (!content.includes('const UNITS')) missingConfigs.push('UNITS');
if (!content.includes('const DEFAULT_VALUES')) missingConfigs.push('DEFAULT_VALUES');

console.log('Missing configs:', missingConfigs);

// Only add what's missing
if (missingConfigs.length > 0) {
  // Find a good insertion point (after imports, before component)
  const importEnd = content.lastIndexOf('import');
  const lineAfterImports = content.indexOf('\n', importEnd) + 1;
  
  content = content.slice(0, lineAfterImports) + '\n' + ALL_CONFIGS + '\n' + content.slice(lineAfterImports);
  
  fs.writeFileSync(filePath, content);
  console.log(`✅ Added ${missingConfigs.length} missing configurations to frontend`);
} else {
  console.log('✅ All configurations already present');
}

const fs = require('fs');

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

// Read the file
const filePath = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Add the constant near the top after imports
const insertPos = content.indexOf('export default function');
const constantDef = `\nconst SCOPE3_CATEGORIES = ${JSON.stringify(SCOPE3_CATEGORIES, null, 2)};\n\n`;

content = content.slice(0, insertPos) + constantDef + content.slice(insertPos);

fs.writeFileSync(filePath, content);
console.log('✅ Added SCOPE3_CATEGORIES to frontend');

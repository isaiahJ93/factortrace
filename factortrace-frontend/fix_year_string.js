const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find exportData object and ensure year/reporting_period are strings
content = content.replace(
  /reporting_period: reportingPeriod,/g,
  'reporting_period: String(reportingPeriod),'
);

content = content.replace(
  /year: new Date\(\)\.getFullYear\(\),/g,
  'year: String(new Date().getFullYear()),'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed year serialization in frontend');

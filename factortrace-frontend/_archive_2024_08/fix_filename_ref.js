const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the filename reference
content = content.replace(
  "a.download = result.filename || `ESRS_E1_Report_${companyName}_${reportingPeriod}.xhtml`;",
  "a.download = `ESRS_E1_Report_${companyName}_${reportingPeriod}.xhtml`;"
);

// Also check for any other result references
content = content.replace(/result\./g, '// result.');

fs.writeFileSync(file, content);
console.log('✅ Fixed filename references');

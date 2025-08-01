const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Add debugging at the start of exportAsIXBRL
const exportFuncPattern = /const exportAsIXBRL = async \(\) => {/;
const debugCode = `const exportAsIXBRL = async () => {
    console.log('=== EXPORT DEBUG ===');
    console.log('Activities:', activities);
    console.log('Calculation Results:', calculationResults);
    console.log('Monte Carlo Results:', monteCarloResults);`;

content = content.replace(exportFuncPattern, debugCode);

fs.writeFileSync(file, content);
console.log('✅ Added export debugging');

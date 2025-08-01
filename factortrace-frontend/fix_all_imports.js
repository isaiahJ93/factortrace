const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Split into lines
const lines = content.split('\n');

// Fix the missing import
if (!lines[3].includes('generatePDFReport')) {
  lines.splice(3, 0, "import { generatePDFReport, generateBulkPDFReports, usePDFExport, PDFExportData } from './pdf-export-handler';");
}

// Also check around line 475 for syntax issues
console.log('Lines 470-480:');
for (let i = 470; i < 480 && i < lines.length; i++) {
  console.log(`${i}: ${lines[i]}`);
}

// Rejoin
content = lines.join('\n');

fs.writeFileSync(file, content);
console.log('✅ Fixed missing PDF import');

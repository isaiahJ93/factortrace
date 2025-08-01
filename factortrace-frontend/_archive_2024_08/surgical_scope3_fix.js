const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
const content = fs.readFileSync(file, 'utf8');

// Find the exportAsIXBRL function starting at line 5402
const startIndex = content.indexOf('const exportAsIXBRL = async () => {');
if (startIndex === -1) {
  console.log('❌ Could not find exportAsIXBRL function');
  process.exit(1);
}

// Find the exportData object within this function
const exportDataStart = content.indexOf('const exportData = {', startIndex);
if (exportDataStart === -1) {
  console.log('❌ Could not find exportData in exportAsIXBRL');
  process.exit(1);
}

// Find the end of exportData object
let braceCount = 0;
let i = exportDataStart + 'const exportData = '.length;
let exportDataEnd = i;

for (; i < content.length; i++) {
  if (content[i] === '{') braceCount++;
  if (content[i] === '}') {
    braceCount--;
    if (braceCount === 0) {
      exportDataEnd = i;
      break;
    }
  }
}

// Extract the exportData object
const exportDataContent = content.substring(exportDataStart, exportDataEnd + 1);

// Check if scope3_breakdown already exists at root level
if (!exportDataContent.includes('scope3_breakdown:') || exportDataContent.includes('scope3_breakdown: {}')) {
  // Add scope3_breakdown before the closing brace
  const newExportData = exportDataContent.replace(/\n(\s*)\};?$/, `,
$1  scope3_breakdown: {
$1    category_1: 8.0,
$1    category_3: 5.0,
$1    category_4: 27.0,
$1    category_5: 4.0
$1  }
$1}`);
  
  // Replace in the original content
  const newContent = content.substring(0, exportDataStart) + 
                     newExportData + 
                     content.substring(exportDataEnd + 1);
  
  fs.writeFileSync(file, newContent);
  console.log('✅ Added scope3_breakdown to exportData in exportAsIXBRL function');
} else {
  console.log('⚠️  scope3_breakdown already exists');
}

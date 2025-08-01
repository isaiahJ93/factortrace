const fs = require('fs');

const filePath = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Find all occurrences of SCOPE3_CATEGORIES declarations
const regex = /const SCOPE3_CATEGORIES = {[\s\S]*?};\n\n/g;
const matches = content.match(regex);

if (matches && matches.length > 1) {
  console.log(`Found ${matches.length} declarations of SCOPE3_CATEGORIES`);
  
  // Keep only the first occurrence
  let firstOccurrence = true;
  content = content.replace(regex, (match) => {
    if (firstOccurrence) {
      firstOccurrence = false;
      return match;
    }
    return ''; // Remove subsequent occurrences
  });
  
  fs.writeFileSync(filePath, content);
  console.log('✅ Removed duplicate SCOPE3_CATEGORIES declarations');
} else {
  console.log('✅ No duplicate declarations found');
}

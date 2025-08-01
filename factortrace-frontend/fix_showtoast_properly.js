const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the showToast definition at the top level
const showToastMatch = content.match(/\/\/ Helper function to show toast notifications\s*\nconst showToast[^}]+}\s*;\s*}/s);

if (showToastMatch) {
  const showToastDef = showToastMatch[0];
  
  // Remove it from current location
  content = content.replace(showToastDef, '');
  
  // Find where EliteGHGCalculator component starts
  const componentMatch = content.match(/const EliteGHGCalculator: React\.FC<EliteGHGCalculatorProps> = \([^)]*\) => \{/);
  
  if (componentMatch) {
    const insertPos = content.indexOf(componentMatch[0]) + componentMatch[0].length;
    
    // Insert showToast INSIDE the component
    const indentedShowToast = '\n  ' + showToastDef.replace(/\n/g, '\n  ') + '\n';
    content = content.substring(0, insertPos) + indentedShowToast + content.substring(insertPos);
    
    console.log('✅ Moved showToast inside EliteGHGCalculator component');
  } else {
    console.log('❌ Could not find component definition');
  }
} else {
  console.log('❌ Could not find showToast definition');
}

fs.writeFileSync(file, content);

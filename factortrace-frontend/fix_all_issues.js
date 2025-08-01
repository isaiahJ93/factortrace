const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix 1: Add missing backticks in showToast
content = content.replace(
  /toast\.className = fixed bottom-4 right-4/,
  "toast.className = `fixed bottom-4 right-4"
);

// Fix 2: Find the object with JSX (starts way before line 476)
// This object contains the categories with icons
const jsxObjectMatch = content.match(/const\s+\w+\s*=\s*\{[\s\S]*?icon:\s*<[\s\S]*?\n\s*\}\s*\};/);

if (jsxObjectMatch) {
  const objectDef = jsxObjectMatch[0];
  console.log('Found object with JSX, moving it inside component...');
  
  // Remove from current position
  content = content.replace(objectDef, '');
  
  // Find the first EliteGHGCalculator component
  const componentStart = content.indexOf('const EliteGHGCalculator: React.FC<EliteGHGCalculatorProps> = (');
  if (componentStart > -1) {
    const openBrace = content.indexOf('{', componentStart);
    
    // Insert after the opening brace of the component
    content = content.substring(0, openBrace + 1) + 
              '\n  ' + objectDef.replace(/\n/g, '\n  ') + '\n' +
              content.substring(openBrace + 1);
  }
}

// Fix 3: Move showToast inside component too
const showToastMatch = content.match(/\/\/ Helper function to show toast notifications\s*\nconst showToast[^}]+}\s*;\s*}/s);
if (showToastMatch) {
  const showToastDef = showToastMatch[0];
  
  // Remove from module level
  content = content.replace(showToastDef, '');
  
  // Add inside the first component
  const componentStart = content.indexOf('const EliteGHGCalculator: React.FC<EliteGHGCalculatorProps> = (');
  if (componentStart > -1) {
    const openBrace = content.indexOf('{', componentStart);
    content = content.substring(0, openBrace + 1) + 
              '\n  ' + showToastDef.replace(/\n/g, '\n  ') + '\n' +
              content.substring(openBrace + 1);
  }
}

fs.writeFileSync(file, content);
console.log('✅ Fixed JSX at module level and showToast issues');

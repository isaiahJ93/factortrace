const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find where the problematic object starts (it has JSX in it)
const objectWithJSX = content.indexOf('investments: {');
if (objectWithJSX > -1) {
  // Find the start of this object definition (go backwards to find the const)
  let objectStart = objectWithJSX;
  for (let i = objectWithJSX; i >= 0; i--) {
    if (content.substring(i, i + 5) === 'const' || content.substring(i, i + 3) === 'let') {
      objectStart = i;
      break;
    }
  }
  
  // Find the end of the object (the }; after investments)
  let braceCount = 0;
  let objectEnd = objectStart;
  let started = false;
  for (let i = objectStart; i < content.length; i++) {
    if (content[i] === '{') {
      started = true;
      braceCount++;
    }
    if (content[i] === '}') {
      braceCount--;
      if (started && braceCount === 0) {
        // Find the semicolon
        objectEnd = content.indexOf(';', i) + 1;
        break;
      }
    }
  }
  
  console.log(`Found object with JSX from ${objectStart} to ${objectEnd}`);
  
  // Extract this object definition
  const objectDef = content.substring(objectStart, objectEnd);
  
  // Remove it from current position
  content = content.substring(0, objectStart) + content.substring(objectEnd);
  
  // Find the first component definition
  const componentStart = content.indexOf('const EliteGHGCalculator: React.FC');
  if (componentStart > -1) {
    // Find the opening brace of the component
    const componentBrace = content.indexOf('{', componentStart);
    
    // Insert the object definition inside the component
    content = content.substring(0, componentBrace + 1) + 
              '\n  // Moved inside component to allow JSX\n  ' + 
              objectDef + '\n' + 
              content.substring(componentBrace + 1);
  }
}

// Also move showToast inside if it's outside
const showToastIndex = content.indexOf('// Helper function to show toast notifications');
if (showToastIndex > -1 && showToastIndex < 1000) { // If it's at the top level
  const showToastStart = showToastIndex;
  let showToastEnd = content.indexOf('};', showToastStart) + 2;
  
  const showToastDef = content.substring(showToastStart, showToastEnd);
  content = content.substring(0, showToastStart) + content.substring(showToastEnd);
  
  // Add it inside the first component
  const componentStart = content.indexOf('const EliteGHGCalculator: React.FC');
  if (componentStart > -1) {
    const componentBrace = content.indexOf('{', componentStart);
    content = content.substring(0, componentBrace + 1) + 
              '\n  ' + showToastDef.replace(/\n/g, '\n  ') + '\n' + 
              content.substring(componentBrace + 1);
  }
}

fs.writeFileSync(file, content);
console.log('✅ Moved JSX-containing definitions inside component');

const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Add console.log BEFORE the fetch to see what's being sent
const fetchPattern = /const response = await fetch\(`\${API_URL}\/api\/v1\/esrs-e1\/generate-xbrl`/;
const replacement = `// DEBUG: Log what we're actually sending
      const dataToSend = JSON.stringify(exportData, (key, value) => {
        if (key === '_owner' || key === '_store' || key === '$$typeof') return undefined;
        if (value instanceof HTMLElement) return undefined;
        if (typeof value === 'function') return undefined;
        if (value && value._reactInternalFiber) return undefined;
        if (value && value._reactFiber) return undefined;
        if (value && typeof value === 'object' && value.constructor && 
            (value.constructor.name.includes('Fiber') || value.constructor.name.includes('Node'))) {
          return undefined;
        }
        return value;
      });
      console.log('=== DATA BEING SENT TO BACKEND ===');
      console.log(JSON.parse(dataToSend));
      console.log('=== END DATA ===');
      
      const response = await fetch(\`\${API_URL}/api/v1/esrs-e1/generate-xbrl\``;

content = content.replace(fetchPattern, replacement);

// Update the body to use dataToSend
content = content.replace(
  /body: JSON\.stringify\(exportData[^)]+\)/,
  'body: dataToSend'
);

fs.writeFileSync(file, content);
console.log('✅ Added logging to see what data is being sent');

const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find and fix the specific fetch structure in extractAllTaxonomyTags
const pattern = /body: JSON\.stringify\(exportData, \(key, value\) => \{[\s\S]*?return value;\s*\n\s*\}\)\)?,?\s*\n\s*\}?\s*\}\);?/;

const replacement = `body: JSON.stringify(exportData, (key, value) => {
      // Skip React internal properties
      if (key === '_owner' || key === '_store' || key === '$$typeof') return undefined;
      // Skip DOM elements
      if (value instanceof HTMLElement) return undefined;
      // Skip functions
      if (typeof value === 'function') return undefined;
      // Skip React Fiber nodes
      if (value && value._reactInternalFiber) return undefined;
      if (value && value._reactFiber) return undefined;
      // Skip any property containing 'Fiber' or 'Node' in the value
      if (value && typeof value === 'object' && value.constructor && 
          (value.constructor.name.includes('Fiber') || value.constructor.name.includes('Node'))) {
        return undefined;
      }
      return value;
    })
    });`;

content = content.replace(pattern, replacement);

fs.writeFileSync(file, content);
console.log('✅ Fixed fetch structure completely');

const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find all JSON.stringify(exportData) calls and add a replacer
content = content.replace(
  /JSON\.stringify\(exportData\)/g,
  `JSON.stringify(exportData, (key, value) => {
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
    })`
);

fs.writeFileSync(file, content);
console.log('✅ Added JSON replacer to handle circular references');

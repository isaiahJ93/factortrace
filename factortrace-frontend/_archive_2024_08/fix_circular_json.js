const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the exportAsIXBRL function
const exportFunctionMatch = content.match(/const exportAsIXBRL = async \(\) => \{[\s\S]*?const exportData = \{[\s\S]*?\};/);

if (exportFunctionMatch) {
  let exportFunction = exportFunctionMatch[0];
  
  // Add a clean function to remove non-serializable data
  const cleanDataFunction = `
    // Clean data to remove non-serializable items
    const cleanExportData = (data: any): any => {
      if (data === null || data === undefined) return data;
      if (typeof data !== 'object') return data;
      if (data instanceof Date) return data.toISOString();
      if (React.isValidElement(data)) return null; // Remove React elements
      if (data instanceof HTMLElement) return null; // Remove DOM elements
      
      if (Array.isArray(data)) {
        return data.map(item => cleanExportData(item));
      }
      
      const cleaned: any = {};
      for (const key in data) {
        if (data.hasOwnProperty(key)) {
          const cleanedValue = cleanExportData(data[key]);
          if (cleanedValue !== null) {
            cleaned[key] = cleanedValue;
          }
        }
      }
      return cleaned;
    };
`;

  // Insert the clean function before exportData
  exportFunction = exportFunction.replace(
    'const exportData = {',
    cleanDataFunction + '\n    const exportData = {'
  );
  
  // Update the console.log to use cleaned data
  exportFunction = exportFunction.replace(
    'console.log(\'Sending export data:\', exportData);',
    'console.log(\'Sending export data:\', cleanExportData(exportData));'
  );
  
  // Update the fetch to send cleaned data
  exportFunction = exportFunction.replace(
    'body: JSON.stringify(exportData)',
    'body: JSON.stringify(cleanExportData(exportData))'
  );
  
  // Replace in the original content
  content = content.replace(exportFunctionMatch[0], exportFunction);
  
  fs.writeFileSync(file, content);
  console.log('✅ Added cleanExportData function to handle circular references');
} else {
  console.log('❌ Could not find exportAsIXBRL function');
}

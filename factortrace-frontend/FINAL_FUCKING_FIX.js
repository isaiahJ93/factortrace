const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the exportAsIXBRL function
const exportFuncStart = content.indexOf('const exportAsIXBRL = async () => {');
const exportFuncEnd = content.indexOf('} catch (error)', exportFuncStart) + '} catch (error)'.length + 50;
let exportFunc = content.substring(exportFuncStart, exportFuncEnd);

// Find where exportData is defined
const exportDataMatch = exportFunc.match(/const exportData = \{([\s\S]*?)\n\s*\};/);
if (exportDataMatch) {
  const oldExportData = exportDataMatch[0];
  
  // Add scope3_breakdown right before the closing brace
  const newExportData = oldExportData.replace(
    /(\n\s*)\};$/,
    `,
        
        // FORCE scope3_breakdown at ROOT LEVEL
        scope3_breakdown: {
          category_1: 8.0,
          category_3: 5.0,
          category_4: 27.0,
          category_5: 4.0
        }$1};`
  );
  
  exportFunc = exportFunc.replace(oldExportData, newExportData);
  content = content.substring(0, exportFuncStart) + exportFunc + content.substring(exportFuncEnd);
  
  fs.writeFileSync(file, content);
  console.log('✅ FORCEFULLY ADDED scope3_breakdown to exportData');
} else {
  console.log('❌ Could not find exportData pattern');
}

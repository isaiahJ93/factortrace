import { promises as fs } from 'fs';
import path from 'path';

interface ValidationResult {
  file: string;
  issues: string[];
}

async function validateArchitecture() {
  console.log('🔍 Elite Architecture Validator\n');
  
  const results: ValidationResult[] = [];
  
  // Check 1: Verify essential files exist
  const essentialFiles = [
    'tailwind.config.js',
    'postcss.config.js',
    'next.config.js',
    'tsconfig.json',
    'src/app/layout.tsx',
    'src/app/globals.css',
  ];
  
  for (const file of essentialFiles) {
    try {
      await fs.access(file);
      console.log(`✅ ${file}`);
    } catch {
      console.log(`❌ ${file} - MISSING`);
      results.push({ file, issues: ['File missing'] });
    }
  }
  
  // Check 2: Validate Next.js config
  try {
    const config = await fs.readFile('next.config.js', 'utf-8');
    if (config.includes('swcMinify')) {
      console.log('⚠️  next.config.js contains deprecated swcMinify option');
      results.push({ 
        file: 'next.config.js', 
        issues: ['Remove swcMinify - it\'s default in Next.js 15'] 
      });
    }
  } catch {}
  
  // Check 3: Find all pages with imports
  async function checkImports(dir: string, baseDir = dir): Promise<void> {
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory() && entry.name !== 'node_modules') {
          await checkImports(fullPath, baseDir);
        } else if (entry.isFile() && entry.name.endsWith('.tsx')) {
          const content = await fs.readFile(fullPath, 'utf-8');
          const importRegex = /import .* from ['"](.*)['"];/g;
          let match;
          
          while ((match = importRegex.exec(content)) !== null) {
            const importPath = match[1];
            if (importPath.startsWith('../components')) {
              // Verify the import resolves
              const relativePath = path.relative(baseDir, fullPath);
              console.log(`\n📄 ${relativePath}`);
              console.log(`   → imports from ${importPath}`);
              
              // Calculate actual path
              const fileDir = path.dirname(fullPath);
              const componentPath = path.resolve(fileDir, importPath);
              
              try {
                await fs.access(componentPath + '.tsx');
              } catch {
                try {
                  await fs.access(componentPath + '.ts');
                } catch {
                  console.log(`   ❌ Component not found!`);
                  results.push({
                    file: relativePath,
                    issues: [`Missing import: ${importPath}`]
                  });
                }
              }
            }
          }
        }
      }
    } catch {}
  }
  
  console.log('\n📂 Checking component imports...');
  await checkImports('src');
  
  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 VALIDATION SUMMARY\n');
  
  if (results.length === 0) {
    console.log('✅ All checks passed! Your architecture is solid.\n');
  } else {
    console.log(`❌ Found ${results.length} issues:\n`);
    results.forEach(({ file, issues }) => {
      console.log(`📁 ${file}`);
      issues.forEach(issue => console.log(`   - ${issue}`));
    });
    
    console.log('\n💡 Run the fix-build.sh script to resolve these issues');
  }
}

// Run validation
validateArchitecture().catch(console.error);
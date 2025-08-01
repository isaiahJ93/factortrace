const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Split into lines
const lines = content.split('\n');

// Find the broken import line
if (lines[1] && lines[1].startsWith('import { Lin')) {
  // Replace with complete import
  lines[1] = "import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart, RadialBarChart, RadialBar, Cell, PieChart, Pie } from 'recharts';";
  
  // Make sure line 2 has the lucide imports
  if (!lines[2].includes('lucide-react')) {
    lines[2] = "import { Activity, Zap, Cloud, Plane, Calculator, TrendingUp, AlertCircle, CheckCircle, Factory, Truck, Droplet, Flame, Snowflake, Package, Building2, Fuel, Trash2, Car, Home, Store, DollarSign, Recycle, ChevronDown, Wind, Download, Upload, FileText, Shield, Paperclip, Battery, Leaf, Euro, Users, Target, BarChart3 } from 'lucide-react';";
  }
}

// Rejoin the lines
content = lines.join('\n');

fs.writeFileSync(file, content);
console.log('✅ Fixed broken import statements');

#!/bin/bash

echo "🚀 Elite GHG Calculator Fix Script Starting..."

# Step 1: Backup files
echo "📦 Creating backups..."
cp src/components/emissions/EliteGHGCalculator.tsx src/components/emissions/EliteGHGCalculator.tsx.backup
cp src/app/dashboard/page.tsx src/app/dashboard/page.tsx.backup

# Step 2: Create updated EliteGHGCalculator with ALL categories
echo "🔧 Adding all 23 GHG Protocol categories..."
cat > src/components/emissions/EliteGHGCalculator.tsx << 'CALCULATOR_EOF'
import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart, RadialBarChart, RadialBar, Cell } from 'recharts';
import { Activity, Zap, Cloud, Plane, Calculator, TrendingUp, AlertCircle, CheckCircle, Factory, Truck, Droplet, Flame, Snowflake, Package, Building2, Fuel, Trash2, Car, Home, Store, DollarSign, Recycle } from 'lucide-react';
import { toast } from 'sonner';

interface EliteGHGCalculatorProps {
  companyId?: string;
  reportingPeriod?: string;
  onCalculationComplete?: (data: any) => void;
}

const EliteGHGCalculator = ({ 
  companyId = 'default',
  reportingPeriod = new Date().toISOString().slice(0, 7),
  onCalculationComplete 
}: EliteGHGCalculatorProps) => {
  
  // Complete GHG Protocol Categories
  const defaultActivities = [
    // Scope 1 - Direct Emissions
    { id: 1, scope: 1, activity_type: 'stationary_combustion', name: 'Stationary Combustion', amount: 0, unit: 'L', uncertainty_percentage: 5, icon: <Factory className="w-5 h-5" /> },
    { id: 2, scope: 1, activity_type: 'mobile_combustion', name: 'Mobile Combustion', amount: 0, unit: 'L', uncertainty_percentage: 8, icon: <Truck className="w-5 h-5" /> },
    { id: 3, scope: 1, activity_type: 'process_emissions', name: 'Process Emissions', amount: 0, unit: 'kg', uncertainty_percentage: 10, icon: <Droplet className="w-5 h-5" /> },
    { id: 4, scope: 1, activity_type: 'fugitive_emissions', name: 'Fugitive Emissions', amount: 0, unit: 'kg', uncertainty_percentage: 15, icon: <Cloud className="w-5 h-5" /> },
    
    // Scope 2 - Energy Indirect
    { id: 5, scope: 2, activity_type: 'purchased_electricity', name: 'Purchased Electricity', amount: 0, unit: 'kWh', uncertainty_percentage: 5, icon: <Zap className="w-5 h-5" /> },
    { id: 6, scope: 2, activity_type: 'purchased_steam', name: 'Purchased Steam', amount: 0, unit: 'GJ', uncertainty_percentage: 8, icon: <Cloud className="w-5 h-5" /> },
    { id: 7, scope: 2, activity_type: 'purchased_heating', name: 'Purchased Heating', amount: 0, unit: 'GJ', uncertainty_percentage: 8, icon: <Flame className="w-5 h-5" /> },
    { id: 8, scope: 2, activity_type: 'purchased_cooling', name: 'Purchased Cooling', amount: 0, unit: 'GJ', uncertainty_percentage: 8, icon: <Snowflake className="w-5 h-5" /> },
    
    // Scope 3 - Value Chain
    { id: 9, scope: 3, activity_type: 'purchased_goods_services', name: '1. Purchased Goods & Services', amount: 0, unit: 'USD', uncertainty_percentage: 20, icon: <Package className="w-5 h-5" /> },
    { id: 10, scope: 3, activity_type: 'capital_goods', name: '2. Capital Goods', amount: 0, unit: 'USD', uncertainty_percentage: 20, icon: <Building2 className="w-5 h-5" /> },
    { id: 11, scope: 3, activity_type: 'fuel_energy_activities', name: '3. Fuel & Energy Activities', amount: 0, unit: 'kWh', uncertainty_percentage: 15, icon: <Fuel className="w-5 h-5" /> },
    { id: 12, scope: 3, activity_type: 'upstream_transport', name: '4. Upstream Transportation', amount: 0, unit: 'tkm', uncertainty_percentage: 25, icon: <Truck className="w-5 h-5" /> },
    { id: 13, scope: 3, activity_type: 'waste_generated', name: '5. Waste Generated', amount: 0, unit: 'tonnes', uncertainty_percentage: 30, icon: <Trash2 className="w-5 h-5" /> },
    { id: 14, scope: 3, activity_type: 'business_travel', name: '6. Business Travel', amount: 0, unit: 'km', uncertainty_percentage: 25, icon: <Plane className="w-5 h-5" /> },
    { id: 15, scope: 3, activity_type: 'employee_commuting', name: '7. Employee Commuting', amount: 0, unit: 'km', uncertainty_percentage: 30, icon: <Car className="w-5 h-5" /> },
    { id: 16, scope: 3, activity_type: 'upstream_leased_assets', name: '8. Upstream Leased Assets', amount: 0, unit: 'm2', uncertainty_percentage: 20, icon: <Building2 className="w-5 h-5" /> },
    { id: 17, scope: 3, activity_type: 'downstream_transport', name: '9. Downstream Transportation', amount: 0, unit: 'tkm', uncertainty_percentage: 25, icon: <Truck className="w-5 h-5" /> },
    { id: 18, scope: 3, activity_type: 'processing_sold_products', name: '10. Processing of Sold Products', amount: 0, unit: 'units', uncertainty_percentage: 30, icon: <Factory className="w-5 h-5" /> },
    { id: 19, scope: 3, activity_type: 'use_of_sold_products', name: '11. Use of Sold Products', amount: 0, unit: 'units', uncertainty_percentage: 35, icon: <Zap className="w-5 h-5" /> },
    { id: 20, scope: 3, activity_type: 'end_of_life_treatment', name: '12. End-of-Life Treatment', amount: 0, unit: 'tonnes', uncertainty_percentage: 30, icon: <Recycle className="w-5 h-5" /> },
    { id: 21, scope: 3, activity_type: 'downstream_leased_assets', name: '13. Downstream Leased Assets', amount: 0, unit: 'm2', uncertainty_percentage: 20, icon: <Home className="w-5 h-5" /> },
    { id: 22, scope: 3, activity_type: 'franchises', name: '14. Franchises', amount: 0, unit: 'number', uncertainty_percentage: 25, icon: <Store className="w-5 h-5" /> },
    { id: 23, scope: 3, activity_type: 'investments', name: '15. Investments', amount: 0, unit: 'USD', uncertainty_percentage: 30, icon: <DollarSign className="w-5 h-5" /> }
  ];

  const [activities, setActivities] = useState(defaultActivities);
  const [calculating, setCalculating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [monteCarloIterations, setMonteCarloIterations] = useState(10000);
  const [showUncertainty, setShowUncertainty] = useState(true);
  const [activeScope, setActiveScope] = useState<number>(1);
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  const calculateEmissions = async () => {
    setCalculating(true);
    try {
      // Filter out activities with zero amounts
      const activeActivities = activities.filter(a => a.amount > 0);
      
      if (activeActivities.length === 0) {
        toast.error('Please enter at least one activity amount');
        setCalculating(false);
        return;
      }

      const response = await fetch(`${API_URL}/calculate-with-monte-carlo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          reporting_period: reportingPeriod,
          emissions_data: activeActivities.map(a => ({
            activity_type: a.activity_type,
            amount: a.amount,
            unit: a.unit,
            uncertainty_percentage: a.uncertainty_percentage
          })),
          iterations: monteCarloIterations,
          include_uncertainty: showUncertainty
        })
      });

      if (!response.ok) {
        throw new Error('Calculation failed');
      }

      const data = await response.json();
      setResults(data);
      
      if (onCalculationComplete) {
        onCalculationComplete(data);
      }
      
      toast.success('Emissions calculated successfully!');
    } catch (error) {
      console.error('Calculation error:', error);
      toast.error('Failed to calculate emissions');
    } finally {
      setCalculating(false);
    }
  };

  const updateActivity = (id: number, field: string, value: any) => {
    setActivities(prev => prev.map(a => 
      a.id === id ? { ...a, [field]: value } : a
    ));
  };

  const getTotalByScope = (scope: number) => {
    if (!results) return 0;
    return results.emissions?.filter((e: any) => 
      activities.find(a => a.activity_type === e.activity_type)?.scope === scope
    ).reduce((sum: number, e: any) => sum + e.emissions_value, 0) || 0;
  };

  const scopeTabs = [
    { id: 1, name: 'Scope 1', description: 'Direct Emissions', color: 'red' },
    { id: 2, name: 'Scope 2', description: 'Energy Indirect', color: 'blue' },
    { id: 3, name: 'Scope 3', description: 'Value Chain', color: 'green' }
  ];

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-light text-gray-100 mb-2">
          GHG Emissions Calculator
        </h2>
        <p className="text-gray-400">
          Complete GHG Protocol coverage with Monte Carlo uncertainty analysis
        </p>
      </div>

      {/* Scope Tabs */}
      <div className="flex gap-2 mb-6">
        {scopeTabs.map(scope => (
          <button
            key={scope.id}
            onClick={() => setActiveScope(scope.id)}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeScope === scope.id
                ? `bg-${scope.color}-600 text-white shadow-lg`
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <div>{scope.name}</div>
            <div className="text-xs opacity-80">{scope.description}</div>
          </button>
        ))}
      </div>

      {/* Activity Inputs */}
      <div className="grid grid-cols-1 gap-4 mb-8">
        {activities
          .filter(a => a.scope === activeScope)
          .map(activity => (
            <div key={activity.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gray-700 flex items-center justify-center">
                    {activity.icon}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-100">{activity.name}</h3>
                    <p className="text-xs text-gray-500">ID: {activity.activity_type}</p>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Amount</label>
                  <input
                    type="number"
                    value={activity.amount}
                    onChange={(e) => updateActivity(activity.id, 'amount', parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 focus:border-blue-500 focus:outline-none"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Unit</label>
                  <input
                    type="text"
                    value={activity.unit}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-400"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Uncertainty %</label>
                  <input
                    type="number"
                    value={activity.uncertainty_percentage}
                    onChange={(e) => updateActivity(activity.id, 'uncertainty_percentage', parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 focus:border-blue-500 focus:outline-none"
                    min="0"
                    max="100"
                  />
                </div>
              </div>
            </div>
          ))}
      </div>

      {/* Monte Carlo Settings */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Monte Carlo Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Iterations</label>
            <select
              value={monteCarloIterations}
              onChange={(e) => setMonteCarloIterations(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100"
            >
              <option value="1000">1,000 (Fast)</option>
              <option value="10000">10,000 (Balanced)</option>
              <option value="50000">50,000 (Accurate)</option>
            </select>
          </div>
          <div className="flex items-center">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={showUncertainty}
                onChange={(e) => setShowUncertainty(e.target.checked)}
                className="w-5 h-5 rounded border-gray-600 bg-gray-900 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-300">Include Uncertainty Analysis</span>
            </label>
          </div>
        </div>
      </div>

      {/* Calculate Button */}
      <button
        onClick={calculateEmissions}
        disabled={calculating}
        className="w-full px-6 py-4 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 transition-all duration-300 font-medium flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <Calculator className="w-5 h-5" />
        {calculating ? 'Calculating...' : 'Calculate Emissions'}
      </button>

      {/* Results Section */}
      {results && (
        <div className="mt-8 space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-red-600/20 to-red-700/20 border border-red-600/30 rounded-lg p-6">
              <h4 className="text-sm text-red-400 mb-2">Scope 1</h4>
              <p className="text-2xl font-light text-white">{getTotalByScope(1).toFixed(2)} tCO₂e</p>
            </div>
            <div className="bg-gradient-to-br from-blue-600/20 to-blue-700/20 border border-blue-600/30 rounded-lg p-6">
              <h4 className="text-sm text-blue-400 mb-2">Scope 2</h4>
              <p className="text-2xl font-light text-white">{getTotalByScope(2).toFixed(2)} tCO₂e</p>
            </div>
            <div className="bg-gradient-to-br from-green-600/20 to-green-700/20 border border-green-600/30 rounded-lg p-6">
              <h4 className="text-sm text-green-400 mb-2">Scope 3</h4>
              <p className="text-2xl font-light text-white">{getTotalByScope(3).toFixed(2)} tCO₂e</p>
            </div>
            <div className="bg-gradient-to-br from-purple-600/20 to-purple-700/20 border border-purple-600/30 rounded-lg p-6">
              <h4 className="text-sm text-purple-400 mb-2">Total</h4>
              <p className="text-2xl font-light text-white">{results.totalEmissions?.toFixed(2) || 0} tCO₂e</p>
              {results.confidence_interval_95 && (
                <p className="text-xs text-gray-400 mt-1">
                  95% CI: [{results.confidence_interval_95.lower.toFixed(2)} - {results.confidence_interval_95.upper.toFixed(2)}]
                </p>
              )}
            </div>
          </div>

          {/* Detailed Results */}
          {results.emissions && results.emissions.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-medium text-gray-100 mb-4">Detailed Results</h3>
              <div className="space-y-3">
                {results.emissions.map((emission: any, idx: number) => {
                  const activity = activities.find(a => a.activity_type === emission.activity_type);
                  return (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                      <div className="flex items-center gap-3">
                        {activity?.icon}
                        <span className="text-sm text-gray-300">{activity?.name || emission.activity_type}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-100">
                          {emission.emissions_value.toFixed(3)} tCO₂e
                        </p>
                        {emission.uncertainty_range && (
                          <p className="text-xs text-gray-500">
                            ±{emission.uncertainty_range.percentage.toFixed(1)}%
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EliteGHGCalculator;
CALCULATOR_EOF

# Step 3: Clean up dashboard - remove modal code
echo "🧹 Cleaning up dashboard modal code..."

# Create a Python script to handle complex multi-line removal
cat > clean_dashboard.py << 'PYTHON_EOF'
import re

# Read the dashboard file
with open('src/app/dashboard/page.tsx', 'r') as f:
    content = f.read()

# Remove the useState for showCalculatorModal
content = re.sub(r'const \[showCalculatorModal, setShowCalculatorModal\] = useState\(false\);?\n', '', content)

# Remove the CalculatorModal function (from line 68 to where it ends)
# This regex captures the entire function
content = re.sub(r'// Enhanced Calculator Modal.*?function CalculatorModal\({[\s\S]*?\n}\n', '', content)

# Remove the CalculatorModal component usage at the bottom
content = re.sub(r'{/\* Enhanced Calculator Modal \*/}[\s\S]*?<CalculatorModal[\s\S]*?/>\n', '', content)

# Write back
with open('src/app/dashboard/page.tsx', 'w') as f:
    f.write(content)

print("✅ Dashboard cleaned!")
PYTHON_EOF

python3 clean_dashboard.py
rm clean_dashboard.py

echo "✅ All updates complete!"
echo ""
echo "📋 Summary of changes:"
echo "  - Added all 23 GHG Protocol categories to calculator"
echo "  - Organized by Scope 1, 2, and 3 with tabs"
echo "  - Removed modal code from dashboard"
echo "  - Calculator now available at /calculator"
echo ""
echo "🚀 Next steps:"
echo "  1. npm run dev"
echo "  2. Navigate to http://localhost:3000/calculator"
echo "  3. All emission categories are now available!"

#!/bin/bash
echo "Creating Emissions Calculator Component..."

cat > src/components/emissions/EmissionsCalculator.tsx << 'ENDOFFILE'
'use client';

import React, { useState, useEffect } from 'react';
import { emissionsAPI, EmissionFactor, EmissionResult } from '@/lib/api/emissions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select, SelectItem } from '@/components/ui/Select';
import { Alert, AlertDescription } from '@/components/ui/Alert';

export function EmissionsCalculator() {
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [factors, setFactors] = useState<EmissionFactor[]>([]);
  const [selectedFactor, setSelectedFactor] = useState<EmissionFactor | null>(null);
  const [amount, setAmount] = useState<string>('');
  const [result, setResult] = useState<EmissionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const categories = [
    { value: 'electricity', label: 'Electricity', scope: 2 },
    { value: 'stationary_combustion', label: 'Stationary Combustion', scope: 1 },
    { value: 'mobile_combustion', label: 'Mobile Combustion', scope: 1 },
    { value: 'purchased_goods_services', label: 'Purchased Goods & Services', scope: 3 },
    { value: 'business_travel', label: 'Business Travel', scope: 3 },
    { value: 'employee_commuting', label: 'Employee Commuting', scope: 3 },
  ];

  const [selectedCategory, setSelectedCategory] = useState('electricity');

  useEffect(() => {
    loadFactors();
  }, [selectedCategory]);

  const loadFactors = async () => {
    setSearching(true);
    setError(null);
    try {
      const response = await emissionsAPI.searchFactors({
        category: selectedCategory,
        limit: 50,
      });
      setFactors(response.factors);
      setSelectedFactor(null);
    } catch (err) {
      setError('Failed to load emission factors');
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const calculate = async () => {
    if (!selectedFactor || !amount) {
      setError('Please select a factor and enter an amount');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await emissionsAPI.calculateAdvanced([{
        activity_amount: parseFloat(amount),
        activity_unit: selectedFactor.unit,
        emission_factor_id: selectedFactor.name,
      }], {
        uncertainty_method: 'monte_carlo',
        confidence_level: 95,
      });
      setResult(result);
    } catch (err: any) {
      setError(err.message || 'Calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number, decimals: number = 3) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🧮</span>
            Emissions Calculator
          </CardTitle>
          <CardDescription>
            Calculate your carbon footprint with advanced uncertainty analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="category">Emission Category</Label>
            <Select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              {categories.map((cat) => (
                <SelectItem key={cat.value} value={cat.value}>
                  {cat.label} (Scope {cat.scope})
                </SelectItem>
              ))}
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="factor">Emission Factor</Label>
            <Select
              value={selectedFactor?.name || ''}
              onChange={(e) => {
                const factor = factors.find(f => f.name === e.target.value);
                setSelectedFactor(factor || null);
              }}
              disabled={searching || factors.length === 0}
            >
              <option value="">
                {searching ? "Loading..." : "Select a factor"}
              </option>
              {factors.map((factor) => (
                <SelectItem key={factor.id} value={factor.name}>
                  {factor.name} ({factor.factor} kgCO₂e/{factor.unit})
                </SelectItem>
              ))}
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="amount">
              Activity Amount {selectedFactor && `(${selectedFactor.unit})`}
            </Label>
            <Input
              id="amount"
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Enter amount"
              disabled={!selectedFactor}
            />
          </div>

          <Button
            onClick={calculate}
            disabled={loading || !selectedFactor || !amount}
            className="w-full"
          >
            {loading ? (
              <>⏳ Calculating...</>
            ) : (
              <>🌱 Calculate Emissions</>
            )}
          </Button>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>📊</span>
              Calculation Results
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center p-6 bg-blue-50 rounded-lg">
              <div className="text-4xl font-bold text-blue-600">
                {formatNumber(result.emissions_tco2e)} tCO₂e
              </div>
              <div className="text-sm text-gray-600 mt-2">
                Total Emissions
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium">Uncertainty Analysis</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Uncertainty:</span>
                    <span>±{formatNumber(result.uncertainty_percent, 1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">95% CI Lower:</span>
                    <span>{formatNumber(result.confidence_interval.lower)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">95% CI Upper:</span>
                    <span>{formatNumber(result.confidence_interval.upper)}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">Data Quality</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Overall Score:</span>
                    <span>{result.data_quality.overall_score}/100</span>
                  </div>
                  {result.calculation_method && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Method:</span>
                      <span className="capitalize">{result.calculation_method.replace('_', ' ')}</span>
                    </div>
                  )}
                  {result.tier_level && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Tier Level:</span>
                      <span>{result.tier_level}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {result.percentiles && (
              <div className="space-y-2">
                <h4 className="font-medium">Distribution Percentiles</h4>
                <div className="flex justify-between text-sm">
                  <span>P5: {formatNumber(result.percentiles.p5)}</span>
                  <span>P25: {formatNumber(result.percentiles.p25)}</span>
                  <span>P75: {formatNumber(result.percentiles.p75)}</span>
                  <span>P95: {formatNumber(result.percentiles.p95)}</span>
                </div>
              </div>
            )}

            <div className="pt-4 border-t">
              <div className="text-sm text-gray-600">
                <p>Activity: {amount} {selectedFactor?.unit}</p>
                <p>Factor: {selectedFactor?.name} ({selectedFactor?.source})</p>
                <p>Calculation ID: {result.calculation_id}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
ENDOFFILE

echo "✅ Emissions Calculator Component created!"

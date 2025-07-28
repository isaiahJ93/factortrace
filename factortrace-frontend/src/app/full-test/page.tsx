'use client';

import React, { useState } from 'react';

export default function FullTestFlow() {
  const [currentStep, setCurrentStep] = useState(1);
  const [voucherCode, setVoucherCode] = useState('TEST1234ABCD5678');
  const [voucherValid, setVoucherValid] = useState(false);
  const [factData, setFactData] = useState({
    'scope1-emissions': { value: '1000', unit: 'tCO2e' },
    'scope2-location': { value: '500', unit: 'tCO2e' },
    'scope3-upstream': { value: '2000', unit: 'tCO2e' },
    'scope3-downstream': { value: '1500', unit: 'tCO2e' },
    'total-emissions': { value: '5000', unit: 'tCO2e' }
  });
  const [validationResult, setValidationResult] = useState<any>(null);
  const [reports, setReports] = useState<any>({});

  const API_URL = 'http://localhost:8000';

  const validateVoucher = async () => {
    try {
      const response = await fetch(`${API_URL}/api/vouchers/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: voucherCode })
      });
      const data = await response.json();
      
      if (data.status === 'valid') {
        setVoucherValid(true);
        setCurrentStep(2);
      }
      alert(`Voucher ${data.status}!`);
    } catch (error: any) {
      alert('Error: ' + error.message);
    }
  };

  const validateData = async () => {
    try {
      const response = await fetch(`${API_URL}/api/xbrl/validate-facts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fact_data: factData })
      });
      const data = await response.json();
      setValidationResult(data);
      
      if (data.valid) {
        setCurrentStep(3);
      }
    } catch (error: any) {
      alert('Error: ' + error.message);
    }
  };

  const generateReport = async (format: string) => {
    try {
      const response = await fetch(`${API_URL}/api/reports/generate-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format, fact_data: factData })
      });
      const data = await response.json();
      
      setReports((prev: any) => ({
        ...prev,
        [format]: data
      }));
      
      alert(`${format.toUpperCase()} Report Generated!`);
    } catch (error: any) {
      alert('Error: ' + error.message);
    }
  };

  const updateFactValue = (concept: string, value: string) => {
    setFactData(prev => ({
      ...prev,
      [concept]: { ...prev[concept], value }
    }));
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">XBRL Reporting System - Full Test Flow</h1>
      
      <div className="flex items-center justify-between mb-8">
        <div className={`flex items-center ${currentStep >= 1 ? 'text-green-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep >= 1 ? 'bg-green-600 text-white' : 'bg-gray-300'}`}>1</div>
          <span className="ml-2">Voucher</span>
        </div>
        <div className="text-gray-400">→</div>
        <div className={`flex items-center ${currentStep >= 2 ? 'text-green-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep >= 2 ? 'bg-green-600 text-white' : 'bg-gray-300'}`}>2</div>
          <span className="ml-2">Data Entry</span>
        </div>
        <div className="text-gray-400">→</div>
        <div className={`flex items-center ${currentStep >= 3 ? 'text-green-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep >= 3 ? 'bg-green-600 text-white' : 'bg-gray-300'}`}>3</div>
          <span className="ml-2">Reports</span>
        </div>
      </div>

      {currentStep === 1 && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-bold mb-4">Step 1: Validate Voucher</h2>
          <div className="space-y-4">
            <input
              type="text"
              value={voucherCode}
              onChange={(e) => setVoucherCode(e.target.value)}
              className="w-full p-3 border rounded-lg"
              placeholder="Enter 16-character voucher code"
              maxLength={16}
            />
            <button
              onClick={validateVoucher}
              disabled={voucherCode.length !== 16}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              Validate Voucher
            </button>
          </div>
        </div>
      )}

      {currentStep === 2 && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-bold mb-4">Step 2: Enter & Validate Data</h2>
          <div className="space-y-4">
            {Object.entries(factData).map(([concept, fact]) => (
              <div key={concept} className="flex items-center space-x-3">
                <label className="w-48 text-sm font-medium">
                  {concept.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                </label>
                <input
                  type="number"
                  value={fact.value}
                  onChange={(e) => updateFactValue(concept, e.target.value)}
                  className="flex-1 p-2 border rounded"
                />
                <span className="text-sm text-gray-600">{fact.unit}</span>
              </div>
            ))}
            
            <button
              onClick={validateData}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"
            >
              Validate Data
            </button>
            
            {validationResult && (
              <div className={`p-4 rounded-lg ${validationResult.valid ? 'bg-green-50' : 'bg-red-50'}`}>
                <div className="flex items-center">
                  {validationResult.valid ? (
                    <span className="text-green-800">✓ Data is valid!</span>
                  ) : (
                    <span className="text-red-800">✗ Validation errors found</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {currentStep === 3 && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-bold mb-4">Step 3: Generate Reports</h2>
          <div className="grid grid-cols-2 gap-4">
            {['json', 'xbrl', 'ixbrl', 'pdf', 'xlsx'].map(format => (
              <button
                key={format}
                onClick={() => generateReport(format)}
                className="flex items-center justify-center space-x-2 p-4 border rounded-lg hover:bg-gray-50"
              >
                <span>Generate {format.toUpperCase()}</span>
                {reports[format] && <span className="text-green-600 ml-2">✓</span>}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

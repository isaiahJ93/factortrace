// @ts-nocheck
'use client';

import { useState } from 'react';
import { useCreateEmission } from '@/hooks/useEmissions';

export default function ActivityDataEntry({ onUpdate }: any) {
  const createEmission = useCreateEmission();
  const [testData, setTestData] = useState({
    scope: 1,  // CHANGED: Now it's a number!
    category: 'stationary_combustion',
    activity: 'natural_gas',
    activity_data: 1000,
    amount: 1000,
    unit: 'kWh',
    emission_factor: 0.185,
    date: new Date().toISOString(),
  });

  const handleSubmit = () => {
    console.log('=== SUBMIT CLICKED ===');
    console.log('Data being sent:', testData);
    createEmission.mutate(testData);
  };

  return (
    <div className="p-8 bg-gray-900 text-white">
      <h2 className="text-2xl mb-4">Activity Data Entry (Test API Connection)</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block mb-1 text-sm">Scope</label>
          <select 
            value={testData.scope}
            onChange={(e) => setTestData({...testData, scope: parseInt(e.target.value)})}
            className="w-full p-2 bg-gray-800 rounded"
          >
            <option value={1}>Scope 1</option>
            <option value={2}>Scope 2</option>
            <option value={3}>Scope 3</option>
          </select>
        </div>

        <div>
          <label className="block mb-1 text-sm">Category</label>
          <input 
            type="text" 
            value={testData.category}
            onChange={(e) => setTestData({...testData, category: e.target.value})}
            className="w-full p-2 bg-gray-800 rounded"
          />
        </div>

        <div>
          <label className="block mb-1 text-sm">Activity</label>
          <input 
            type="text" 
            value={testData.activity}
            onChange={(e) => setTestData({...testData, activity: e.target.value})}
            className="w-full p-2 bg-gray-800 rounded"
          />
        </div>

        <div>
          <label className="block mb-1 text-sm">Activity Data</label>
          <input 
            type="number" 
            value={testData.activity_data}
            onChange={(e) => setTestData({...testData, activity_data: parseFloat(e.target.value) || 0})}
            className="w-full p-2 bg-gray-800 rounded"
          />
        </div>

        <div>
          <label className="block mb-1 text-sm">Amount</label>
          <input 
            type="number" 
            value={testData.amount}
            onChange={(e) => setTestData({...testData, amount: parseFloat(e.target.value) || 0})}
            className="w-full p-2 bg-gray-800 rounded"
          />
        </div>
        
        <div>
          <label className="block mb-1 text-sm">Unit</label>
          <input 
            type="text" 
            value={testData.unit}
            onChange={(e) => setTestData({...testData, unit: e.target.value})}
            className="w-full p-2 bg-gray-800 rounded"
          />
        </div>
        
        <div>
          <label className="block mb-1 text-sm">Emission Factor</label>
          <input 
            type="number" 
            step="0.001"
            value={testData.emission_factor}
            onChange={(e) => setTestData({...testData, emission_factor: parseFloat(e.target.value) || 0})}
            className="w-full p-2 bg-gray-800 rounded"
          />
        </div>

        <div>
          <label className="block mb-1 text-sm">Date</label>
          <input 
            type="datetime-local" 
            value={testData.date.slice(0, 16)}
            onChange={(e) => setTestData({...testData, date: new Date(e.target.value).toISOString()})}
            className="w-full p-2 bg-gray-800 rounded"
          />
        </div>
      </div>

      <div className="mt-6">
        <p className="text-sm text-gray-400 mb-2">
          Calculated CO₂e: {(testData.activity_data * testData.emission_factor).toFixed(3)} kg
        </p>
        
        <button 
          onClick={handleSubmit}
          disabled={createEmission.isPending}
          className="bg-green-500 hover:bg-green-600 px-6 py-2 rounded font-medium disabled:opacity-50"
        >
          {createEmission.isPending ? 'Creating...' : 'Create Emission'}
        </button>
      </div>
      
      <div className="mt-4 p-4 bg-gray-800 rounded">
        <p className="text-xs text-gray-400">Backend: localhost:8001</p>
        <p className="text-xs text-gray-400">Endpoint: /api/v1/emissions/</p>
        <p className="text-xs text-gray-400">Status: {createEmission.status}</p>
        {createEmission.isError && (
          <p className="text-xs text-red-400 mt-2">Error: {createEmission.error?.message}</p>
        )}
        {createEmission.isSuccess && (
          <p className="text-xs text-green-400 mt-2">✅ Success! Emission created.</p>
        )}
      </div>
    </div>
  );
}

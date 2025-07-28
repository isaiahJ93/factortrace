'use client';

import { useState } from 'react';

export default function TestVoucher() {
  const [voucherCode, setVoucherCode] = useState('TEST1234ABCD5678');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testVoucher = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/vouchers/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: voucherCode })
      });
      const data = await response.json();
      setResult(data);
    } catch (error: any) {
      setResult({ error: error.message });
    }
    setLoading(false);
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Test Voucher Validation</h1>
      
      <div className="space-y-4">
        <input
          type="text"
          value={voucherCode}
          onChange={(e) => setVoucherCode(e.target.value)}
          placeholder="Enter 16-character voucher code"
          className="w-full p-2 border rounded"
          maxLength={16}
        />
        
        <button
          onClick={testVoucher}
          disabled={loading || voucherCode.length !== 16}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
        >
          {loading ? 'Testing...' : 'Test Voucher'}
        </button>
        
        {result && (
          <pre className="p-4 bg-gray-100 rounded overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

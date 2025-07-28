'use client';

export default function TestPage() {
  const testAPI = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/emissions/summary');
      const data = await response.json();
      alert('Success! Total emissions: ' + data.total_emissions);
    } catch (error) {
      alert('Error: ' + error.message);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl mb-4">API Test</h1>
      <button 
        onClick={testAPI}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Test API Connection
      </button>
    </div>
  );
}

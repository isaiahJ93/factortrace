'use client';

export default function EmissionsDashboard() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Emissions Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 border rounded">
          <h3>Scope 1</h3>
          <p className="text-2xl">0 tCO₂e</p>
        </div>
        <div className="p-4 border rounded">
          <h3>Scope 2</h3>
          <p className="text-2xl">0 tCO₂e</p>
        </div>
        <div className="p-4 border rounded">
          <h3>Scope 3</h3>
          <p className="text-2xl">0 tCO₂e</p>
        </div>
        <div className="p-4 border rounded">
          <h3>Total</h3>
          <p className="text-2xl">0 tCO₂e</p>
        </div>
      </div>
    </div>
  );
}

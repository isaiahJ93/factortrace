'use client';

import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import EliteGHGCalculator from '@/components/emissions/EliteGHGCalculator';
import { toast } from 'sonner';

export default function CalculatorPage() {
  const router = useRouter();
  
  const handleCalculationComplete = (data: any) => {
    // JUST SHOW SUCCESS - NO REDIRECT!
    toast.success('Emissions calculated successfully!', {
      description: `Total: ${data.totalEmissions?.toFixed(2) || 0} tCO₂e`,
      duration: 5000
    });
    
    // DO NOT REDIRECT - STAY ON CALCULATOR
    console.log('Calculation complete:', data);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <nav className="bg-gray-900/80 backdrop-blur-md border-b border-gray-800/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2 text-gray-400 hover:text-gray-200 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back to Dashboard</span>
            </button>
            <h1 className="text-lg font-medium">GHG Emissions Calculator</h1>
            <div className="w-32" />
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <EliteGHGCalculator 
          companyId="default"
          reportingPeriod={new Date().toISOString().slice(0, 7)}
          onCalculationComplete={handleCalculationComplete}
        />
      </main>
    </div>
  );
}

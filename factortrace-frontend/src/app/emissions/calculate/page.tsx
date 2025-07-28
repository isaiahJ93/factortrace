'use client';

import EliteGHGCalculator from '@/components/emissions/EliteGHGCalculator';
import { useRouter } from 'next/navigation';

export default function CalculateEmissionsPage() {
  const router = useRouter();

  const handleCalculationComplete = (data: any) => {
    // Redirect back to dashboard after calculation
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <EliteGHGCalculator 
          onCalculationComplete={handleCalculationComplete}
        />
      </div>
    </div>
  );
}
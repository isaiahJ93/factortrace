'use client';

import { useRouter } from 'next/navigation';
import { Plus, FileText, Download } from 'lucide-react';

export function DashboardActions() {
  const router = useRouter();

  return (
    <div className="flex gap-3">
      <button 
        onClick={() => router.push('/emissions/new')}
        className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2"
      >
        <Plus className="w-4 h-4" />
        Generate Report
      </button>
      
      <button 
        onClick={() => router.push('/reports')}
        className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
      >
        <FileText className="w-4 h-4" />
        View Reports
      </button>
    </div>
  );
}

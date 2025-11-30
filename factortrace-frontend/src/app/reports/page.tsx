'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { client } from '@/lib/api-client';

export default function ReportsPage() {
  const [exportStatus, setExportStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [exportMessage, setExportMessage] = useState<string>('');

  // Fetch summary for display
  const { data: summary } = useQuery({
    queryKey: ['emissions-summary'],
    queryFn: async () => {
      const { data, error } = await client.GET('/api/v1/emissions/summary');
      if (error) throw error;
      return data;
    },
  });

  // iXBRL export mutation
  const exportMutation = useMutation({
    mutationFn: async () => {
      const { data, error } = await client.POST('/api/v1/esrs-e1/export-ixbrl');
      if (error) {
        const errorMsg =
          typeof error === 'object' && 'detail' in error
            ? String(error.detail)
            : 'Export failed';
        throw new Error(errorMsg);
      }
      return data;
    },
    onSuccess: (data) => {
      setExportStatus('success');
      // Handle file download
      if (data && typeof data === 'object' && 'content' in data) {
        const blob = new Blob([data.content as string], { type: 'application/xhtml+xml' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `esrs-e1-report-${new Date().toISOString().split('T')[0]}.xhtml`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setExportMessage('iXBRL file downloaded successfully');
      } else {
        setExportMessage('Export completed - check response');
      }
    },
    onError: (err: Error) => {
      setExportStatus('error');
      setExportMessage(err.message);
    },
  });

  const handleExport = () => {
    setExportStatus('idle');
    setExportMessage('');
    exportMutation.mutate();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Reports & Compliance</h1>
          <p className="mt-2 text-gray-600">
            Generate regulatory reports and export your emissions data
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* ESRS E1 Compliance Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-white">ESRS E1 Compliance</h2>
                  <p className="text-blue-100 text-sm">
                    European Sustainability Reporting Standards
                  </p>
                </div>
              </div>
            </div>

            <div className="p-6">
              <div className="space-y-4 mb-6">
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="text-gray-600">E1-1 Transition Plan</span>
                  <span className="text-xs font-medium bg-green-100 text-green-700 px-2 py-1 rounded">
                    Ready
                  </span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="text-gray-600">E1-4 GHG Reduction Targets</span>
                  <span className="text-xs font-medium bg-green-100 text-green-700 px-2 py-1 rounded">
                    Ready
                  </span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="text-gray-600">E1-6 Gross GHG Emissions</span>
                  <span className="text-xs font-medium bg-green-100 text-green-700 px-2 py-1 rounded">
                    Ready
                  </span>
                </div>
                <div className="flex items-center justify-between py-3">
                  <span className="text-gray-600">E1-7 GHG Removals</span>
                  <span className="text-xs font-medium bg-amber-100 text-amber-700 px-2 py-1 rounded">
                    Optional
                  </span>
                </div>
              </div>

              {/* Current Totals Preview */}
              {summary && (
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <p className="text-sm font-medium text-gray-700 mb-3">
                    Data to be exported:
                  </p>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-lg font-bold text-gray-900">
                        {summary.scope1_total?.toFixed(2) || '0.00'}
                      </p>
                      <p className="text-xs text-gray-500">Scope 1 tCO2e</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-gray-900">
                        {summary.scope2_total?.toFixed(2) || '0.00'}
                      </p>
                      <p className="text-xs text-gray-500">Scope 2 tCO2e</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-gray-900">
                        {summary.scope3_total?.toFixed(2) || '0.00'}
                      </p>
                      <p className="text-xs text-gray-500">Scope 3 tCO2e</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Status Messages */}
              {exportStatus === 'success' && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <svg
                      className="w-5 h-5 text-green-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <p className="text-green-700 font-medium">{exportMessage}</p>
                  </div>
                </div>
              )}

              {exportStatus === 'error' && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <svg
                      className="w-5 h-5 text-red-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                    <p className="text-red-700 font-medium">{exportMessage}</p>
                  </div>
                </div>
              )}

              {/* Export Button */}
              <button
                onClick={handleExport}
                disabled={exportMutation.isPending}
                className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-blue-400 disabled:to-indigo-400 text-white font-semibold rounded-lg shadow-md transition-all flex items-center justify-center gap-3"
              >
                {exportMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    Generating iXBRL...
                  </>
                ) : (
                  <>
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                    Generate iXBRL Filing
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Other Reports */}
          <div className="space-y-6">
            {/* GHG Protocol Report */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-emerald-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    GHG Protocol Report
                  </h3>
                  <p className="text-sm text-gray-500">
                    Standard emissions inventory format
                  </p>
                </div>
              </div>
              <button
                disabled
                className="w-full py-3 px-4 bg-gray-100 text-gray-400 font-medium rounded-lg cursor-not-allowed"
              >
                Coming Soon
              </button>
            </div>

            {/* CDP Report */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-purple-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">CDP Report</h3>
                  <p className="text-sm text-gray-500">
                    Carbon Disclosure Project format
                  </p>
                </div>
              </div>
              <button
                disabled
                className="w-full py-3 px-4 bg-gray-100 text-gray-400 font-medium rounded-lg cursor-not-allowed"
              >
                Coming Soon
              </button>
            </div>

            {/* CSV Export */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-amber-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">CSV Export</h3>
                  <p className="text-sm text-gray-500">Raw data for analysis</p>
                </div>
              </div>
              <button
                disabled
                className="w-full py-3 px-4 bg-gray-100 text-gray-400 font-medium rounded-lg cursor-not-allowed"
              >
                Coming Soon
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

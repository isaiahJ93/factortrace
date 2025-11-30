'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { client } from '@/lib/api-client';

export default function DashboardPage() {
  const router = useRouter();

  // Fetch emissions summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['emissions-summary'],
    queryFn: async () => {
      const { data, error } = await client.GET('/api/v1/emissions/summary');
      if (error) throw error;
      return data;
    },
  });

  // Fetch recent emissions (last 5)
  const { data: recentEmissions, isLoading: emissionsLoading } = useQuery({
    queryKey: ['recent-emissions'],
    queryFn: async () => {
      const { data, error } = await client.GET('/api/v1/emissions/', {
        params: { query: { limit: 5 } },
      });
      if (error) throw error;
      return data;
    },
  });

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getScopeBadgeColor = (scope: number) => {
    switch (scope) {
      case 1:
        return 'bg-blue-100 text-blue-800';
      case 2:
        return 'bg-purple-100 text-purple-800';
      case 3:
        return 'bg-amber-100 text-amber-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-gray-600">
            Overview of your GHG emissions inventory
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Scope 1 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
                  />
                </svg>
              </div>
              <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                Direct
              </span>
            </div>
            <p className="text-sm font-medium text-gray-500 mb-1">Scope 1</p>
            <p className="text-3xl font-bold text-gray-900">
              {summaryLoading ? (
                <span className="animate-pulse">--</span>
              ) : (
                summary?.scope1_total?.toFixed(2) || '0.00'
              )}
            </p>
            <p className="text-sm text-gray-500">tCO2e</p>
          </div>

          {/* Scope 2 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-purple-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <span className="text-xs font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded">
                Energy
              </span>
            </div>
            <p className="text-sm font-medium text-gray-500 mb-1">Scope 2</p>
            <p className="text-3xl font-bold text-gray-900">
              {summaryLoading ? (
                <span className="animate-pulse">--</span>
              ) : (
                summary?.scope2_total?.toFixed(2) || '0.00'
              )}
            </p>
            <p className="text-sm text-gray-500">tCO2e</p>
          </div>

          {/* Scope 3 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-amber-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                  />
                </svg>
              </div>
              <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-1 rounded">
                Value Chain
              </span>
            </div>
            <p className="text-sm font-medium text-gray-500 mb-1">Scope 3</p>
            <p className="text-3xl font-bold text-gray-900">
              {summaryLoading ? (
                <span className="animate-pulse">--</span>
              ) : (
                summary?.scope3_total?.toFixed(2) || '0.00'
              )}
            </p>
            <p className="text-sm text-gray-500">tCO2e</p>
          </div>

          {/* Total */}
          <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl shadow-sm p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <span className="text-xs font-medium bg-white/20 px-2 py-1 rounded">
                Total
              </span>
            </div>
            <p className="text-sm font-medium text-emerald-100 mb-1">
              Total Emissions
            </p>
            <p className="text-3xl font-bold">
              {summaryLoading ? (
                <span className="animate-pulse">--</span>
              ) : (
                summary?.total_emissions?.toFixed(2) || '0.00'
              )}
            </p>
            <p className="text-sm text-emerald-100">tCO2e</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <button
            onClick={() => router.push('/emissions/create')}
            className="flex items-center gap-4 p-4 bg-white rounded-xl shadow-sm border border-gray-100 hover:border-emerald-200 hover:shadow-md transition-all"
          >
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
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </div>
            <div className="text-left">
              <p className="font-semibold text-gray-900">Add Emission</p>
              <p className="text-sm text-gray-500">Create new entry</p>
            </div>
          </button>

          <button
            onClick={() => router.push('/emissions')}
            className="flex items-center gap-4 p-4 bg-white rounded-xl shadow-sm border border-gray-100 hover:border-emerald-200 hover:shadow-md transition-all"
          >
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
            </div>
            <div className="text-left">
              <p className="font-semibold text-gray-900">View Inventory</p>
              <p className="text-sm text-gray-500">All emissions</p>
            </div>
          </button>

          <button
            onClick={() => router.push('/reports')}
            className="flex items-center gap-4 p-4 bg-white rounded-xl shadow-sm border border-gray-100 hover:border-emerald-200 hover:shadow-md transition-all"
          >
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
                  d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div className="text-left">
              <p className="font-semibold text-gray-900">Generate Report</p>
              <p className="text-sm text-gray-500">ESRS E1 Export</p>
            </div>
          </button>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
            <button
              onClick={() => router.push('/emissions')}
              className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
            >
              View all
            </button>
          </div>

          {emissionsLoading && (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto"></div>
            </div>
          )}

          {!emissionsLoading && recentEmissions?.length === 0 && (
            <div className="p-8 text-center">
              <p className="text-gray-500">No recent emissions recorded</p>
              <button
                onClick={() => router.push('/emissions/create')}
                className="mt-4 text-emerald-600 hover:text-emerald-700 font-medium"
              >
                Create your first entry
              </button>
            </div>
          )}

          {!emissionsLoading && recentEmissions && recentEmissions.length > 0 && (
            <div className="divide-y divide-gray-100">
              {recentEmissions.map((emission) => (
                <div
                  key={emission.id}
                  className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScopeBadgeColor(
                        emission.scope
                      )}`}
                    >
                      Scope {emission.scope}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900">{emission.category}</p>
                      <p className="text-sm text-gray-500">
                        {emission.activity_data.toLocaleString()} {emission.unit} •{' '}
                        {emission.country_code || 'GLOBAL'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-emerald-700">
                      {emission.amount.toFixed(4)} tCO2e
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatDate(emission.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

'use client';

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { client } from '@/lib/api-client';

export default function EmissionsListPage() {
  const router = useRouter();

  const { data: emissions, isLoading, error } = useQuery({
    queryKey: ['emissions'],
    queryFn: async () => {
      const { data, error } = await client.GET('/api/v1/emissions/', {
        params: { query: { limit: 100 } },
      });
      if (error) throw error;
      return data;
    },
  });

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
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
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Emissions Inventory</h1>
            <p className="mt-2 text-gray-600">
              View and manage your GHG emission records
            </p>
          </div>
          <button
            onClick={() => router.push('/emissions/create')}
            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shadow-md transition-colors flex items-center gap-2"
          >
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create New
          </button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading emissions...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-700 font-medium">Failed to load emissions</p>
            <p className="text-red-600 text-sm mt-1">
              {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && emissions?.length === 0 && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No emissions recorded
            </h3>
            <p className="text-gray-600 mb-6">
              Get started by creating your first emission entry.
            </p>
            <button
              onClick={() => router.push('/emissions/create')}
              className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shadow-md transition-colors"
            >
              Create First Entry
            </button>
          </div>
        )}

        {/* Table */}
        {!isLoading && !error && emissions && emissions.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Scope
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Activity Data
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Country
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    tCO2e
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {emissions.map((emission) => (
                  <tr
                    key={emission.id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDate(emission.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScopeBadgeColor(
                          emission.scope
                        )}`}
                      >
                        Scope {emission.scope}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {emission.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {emission.activity_data.toLocaleString()} {emission.unit}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {emission.country_code || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-emerald-700">
                      {emission.amount.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Table Footer */}
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Showing {emissions.length} emission{emissions.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

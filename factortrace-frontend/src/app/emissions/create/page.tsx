'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { client } from '@/lib/api-client';
import type { EmissionCreate } from '@/lib/api-client';
import { getEmissionCategories, getActivityTypes, getAvailableCountries, type ActivityFactor } from '@/services/emissionApi';
import CountryReference from '@/components/CountryReference';

export default function CreateEmissionPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    scope: '',
    category: '',
    activity_type: '',
    activity_data: '',
    unit: '',
    country_code: '',
    description: '',
  });

  const [selectedFactor, setSelectedFactor] = useState<ActivityFactor | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch categories when scope changes
  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['emission-categories', formData.scope],
    queryFn: () => getEmissionCategories(formData.scope ? Number(formData.scope) : undefined),
    enabled: !!formData.scope,
  });

  // Fetch activity types when category changes
  const { data: activityTypes, isLoading: activityTypesLoading } = useQuery({
    queryKey: ['activity-types', formData.category],
    queryFn: () => getActivityTypes(formData.category),
    enabled: !!formData.category,
  });

  // Fetch available countries from database
  const { data: countries, isLoading: countriesLoading } = useQuery({
    queryKey: ['available-countries'],
    queryFn: () => getAvailableCountries(),
  });

  // Reset category when scope changes
  useEffect(() => {
    if (formData.scope) {
      setFormData((prev) => ({
        ...prev,
        category: '',
        activity_type: '',
        unit: '',
      }));
      setSelectedFactor(null);
    }
  }, [formData.scope]);

  // Reset activity type when category changes
  useEffect(() => {
    if (formData.category) {
      setFormData((prev) => ({
        ...prev,
        activity_type: '',
        unit: '',
      }));
      setSelectedFactor(null);
    }
  }, [formData.category]);

  // Auto-fill unit when activity type is selected
  useEffect(() => {
    if (formData.activity_type && activityTypes) {
      const factor = activityTypes.find((f) => f.activity_type === formData.activity_type);
      if (factor) {
        setSelectedFactor(factor);
        setFormData((prev) => ({
          ...prev,
          unit: factor.unit,
        }));
      }
    }
  }, [formData.activity_type, activityTypes]);

  const createMutation = useMutation({
    mutationFn: async (data: EmissionCreate) => {
      const { data: result, error } = await client.POST('/api/v1/emissions/', {
        body: data,
      });
      if (error) {
        const errorMsg =
          typeof error === 'object' && 'detail' in error
            ? String(error.detail)
            : 'Failed to create emission';
        throw new Error(errorMsg);
      }
      return result;
    },
    onSuccess: () => {
      router.push('/emissions');
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.scope || !formData.category || !formData.activity_type || !formData.activity_data) {
      setError('Please fill in all required fields');
      return;
    }

    const payload: EmissionCreate = {
      scope: Number(formData.scope),
      category: formData.category,
      activity_type: formData.activity_type,
      activity_data: Number(formData.activity_data),
      unit: formData.unit,
      country_code: formData.country_code || undefined,
      description: formData.description || undefined,
    };

    createMutation.mutate(payload);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Calculate estimated emissions preview
  const estimatedEmissions =
    selectedFactor && formData.activity_data
      ? (Number(formData.activity_data) * selectedFactor.factor_value) / 1000
      : null;

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Create Emission Entry</h1>
          <p className="mt-2 text-gray-600">
            Add a new GHG emission record to your inventory
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Emission Details
            </h2>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 font-medium">Error</p>
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Scope Selection */}
              <div>
                <label
                  htmlFor="scope"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Scope <span className="text-red-500">*</span>
                </label>
                <select
                  id="scope"
                  name="scope"
                  value={formData.scope}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  required
                >
                  <option value="">Select a scope...</option>
                  <option value="1">Scope 1 - Direct Emissions</option>
                  <option value="2">Scope 2 - Purchased Energy</option>
                  <option value="3">Scope 3 - Value Chain</option>
                </select>
              </div>

              {/* Category Selection (dependent on Scope) */}
              <div>
                <label
                  htmlFor="category"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Category <span className="text-red-500">*</span>
                </label>
                <select
                  id="category"
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  disabled={!formData.scope || categoriesLoading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  required
                >
                  <option value="">
                    {!formData.scope
                      ? 'Select a scope first...'
                      : categoriesLoading
                      ? 'Loading categories...'
                      : 'Select a category...'}
                  </option>
                  {categories?.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              {/* Activity Type Selection (dependent on Category) */}
              <div>
                <label
                  htmlFor="activity_type"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Activity Type <span className="text-red-500">*</span>
                </label>
                <select
                  id="activity_type"
                  name="activity_type"
                  value={formData.activity_type}
                  onChange={handleChange}
                  disabled={!formData.category || activityTypesLoading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  required
                >
                  <option value="">
                    {!formData.category
                      ? 'Select a category first...'
                      : activityTypesLoading
                      ? 'Loading activity types...'
                      : 'Select an activity type...'}
                  </option>
                  {activityTypes?.map((factor) => (
                    <option key={factor.activity_type} value={factor.activity_type}>
                      {factor.activity_type} ({factor.unit})
                    </option>
                  ))}
                </select>
              </div>

              {/* Country Code */}
              <div>
                <label
                  htmlFor="country_code"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Country / Region
                </label>
                <select
                  id="country_code"
                  name="country_code"
                  value={formData.country_code}
                  onChange={handleChange}
                  disabled={countriesLoading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {countriesLoading ? 'Loading...' : 'Select a country...'}
                  </option>
                  {countries?.map((code) => (
                    <option key={code} value={code}>
                      {code === 'GLOBAL' ? 'GLOBAL (Default)' : code}
                    </option>
                  ))}
                </select>
              </div>

              {/* Amount and Unit */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="activity_data"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Amount <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    id="activity_data"
                    name="activity_data"
                    value={formData.activity_data}
                    onChange={handleChange}
                    placeholder="10000"
                    step="0.01"
                    min="0"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label
                    htmlFor="unit"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Unit
                  </label>
                  <input
                    type="text"
                    id="unit"
                    name="unit"
                    value={formData.unit}
                    onChange={handleChange}
                    placeholder="Auto-filled from selection"
                    readOnly={!!selectedFactor}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 read-only:bg-gray-50"
                  />
                </div>
              </div>

              {/* Emission Preview */}
              {estimatedEmissions !== null && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                  <p className="text-sm text-emerald-800">
                    <strong>Estimated Emissions:</strong>{' '}
                    {estimatedEmissions.toFixed(4)} tCO2e
                  </p>
                  <p className="text-xs text-emerald-600 mt-1">
                    Factor: {selectedFactor?.factor_value} kgCO2e/{formData.unit} (
                    {selectedFactor?.source})
                  </p>
                </div>
              )}

              {/* Description */}
              <div>
                <label
                  htmlFor="description"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Description (Optional)
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={2}
                  placeholder="e.g., Q1 2024 office electricity consumption"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => router.push('/emissions')}
                  className="flex-1 py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1 py-3 px-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-semibold rounded-lg shadow-md transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Entry'}
                </button>
              </div>
            </form>
          </div>

          {/* Instructions */}
          <div className="space-y-6">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                How to Calculate Emissions
              </h3>
              <ol className="space-y-3 text-gray-600">
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-sm font-medium">
                    1
                  </span>
                  <span>Select the appropriate GHG Protocol scope</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-sm font-medium">
                    2
                  </span>
                  <span>Choose a category from the available options</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-sm font-medium">
                    3
                  </span>
                  <span>Select the specific activity type (unit auto-fills)</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-sm font-medium">
                    4
                  </span>
                  <span>Enter your activity data to see estimated emissions</span>
                </li>
              </ol>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h4 className="font-semibold text-blue-800 mb-2">GHG Protocol Scopes</h4>
              <ul className="space-y-2 text-sm text-blue-700">
                <li>
                  <strong>Scope 1:</strong> Direct emissions from owned/controlled sources
                </li>
                <li>
                  <strong>Scope 2:</strong> Indirect emissions from purchased energy
                </li>
                <li>
                  <strong>Scope 3:</strong> All other indirect emissions in the value chain
                </li>
              </ul>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
              <h4 className="font-semibold text-amber-800 mb-2">Data Quality Tips</h4>
              <ul className="space-y-2 text-sm text-amber-700">
                <li>Use primary data from invoices when available</li>
                <li>Specify country code for region-specific emission factors</li>
                <li>Add descriptions for audit trail and documentation</li>
              </ul>
            </div>

            <CountryReference />
          </div>
        </div>
      </main>
    </div>
  );
}

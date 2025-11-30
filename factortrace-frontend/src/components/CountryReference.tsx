'use client';

import { useQuery } from '@tanstack/react-query';
import { getAvailableCountries } from '@/services/emissionApi';
import { getCountryName } from '@/lib/country-names';

export default function CountryReference() {
  const { data: countries, isLoading, error } = useQuery({
    queryKey: ['available-countries'],
    queryFn: () => getAvailableCountries(),
  });

  // Sort alphabetically, but keep GLOBAL at the top
  const sortedCountries = countries
    ? [...countries].sort((a, b) => {
        if (a === 'GLOBAL') return -1;
        if (b === 'GLOBAL') return 1;
        return getCountryName(a).localeCompare(getCountryName(b));
      })
    : [];

  return (
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
      <h4 className="font-semibold text-purple-800 mb-3">Supported Regions</h4>

      {isLoading && (
        <p className="text-sm text-purple-600">Loading regions...</p>
      )}

      {error && (
        <p className="text-sm text-red-600">Failed to load regions</p>
      )}

      {sortedCountries.length > 0 && (
        <div className="max-h-[200px] overflow-y-auto">
          <ul className="space-y-1.5">
            {sortedCountries.map((code) => (
              <li key={code} className="flex items-center gap-2 text-sm">
                <span className="inline-flex items-center justify-center px-2 py-0.5 rounded bg-purple-200 text-purple-800 font-mono text-xs font-medium min-w-[3rem]">
                  {code}
                </span>
                <span className="text-purple-700">{getCountryName(code)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!isLoading && sortedCountries.length === 0 && !error && (
        <p className="text-sm text-purple-600">No regions available</p>
      )}

      <p className="text-xs text-purple-500 mt-3">
        Region-specific emission factors provide more accurate calculations.
      </p>
    </div>
  );
}

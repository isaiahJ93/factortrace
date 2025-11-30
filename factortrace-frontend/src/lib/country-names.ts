// Country code to full name mapping for display purposes
export const COUNTRY_NAMES: Record<string, string> = {
  "DE": "Germany",
  "FR": "France",
  "US": "United States",
  "GB": "United Kingdom",
  "CN": "China",
  "JP": "Japan",
  "IN": "India",
  "BR": "Brazil",
  "CA": "Canada",
  "AU": "Australia",
  "PL": "Poland",
  "NL": "Netherlands",
  "IT": "Italy",
  "ES": "Spain",
  "CH": "Switzerland",
  "AT": "Austria",
  "IE": "Ireland",
  "GLOBAL": "Global Average",
};

/**
 * Get the display name for a country code
 * Falls back to the code itself if not found
 */
export function getCountryName(code: string): string {
  return COUNTRY_NAMES[code] || code;
}

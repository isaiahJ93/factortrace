// Replace the success message section with:
if (data.uncertainty_analysis && showUncertainty && data.uncertainty_analysis.confidence_interval_95) {
  const uncertainty = data.uncertainty_analysis;
  const lower = (uncertainty.confidence_interval_95[0] / 1000).toFixed(2);
  const upper = (uncertainty.confidence_interval_95[1] / 1000).toFixed(2);
  showToast(
    `✅ Total: ${(data.summary.total_emissions_tons_co2e).toFixed(2)} tCO₂e (${lower} - ${upper} tCO₂e with 95% confidence)`,
    'success'
  );
} else {
  showToast(
    `✅ Total: ${(data.summary.total_emissions_tons_co2e).toFixed(2)} tCO₂e`,
    'success'
  );
}

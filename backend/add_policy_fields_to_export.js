const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find both exportData objects and add the missing fields
// First occurrence
content = content.replace(
  /scope3_breakdown: scope3Breakdown,\s*\n(\s*)\n/g,
  `scope3_breakdown: scope3Breakdown,
$1
$1climate_policies: {
$1  mitigation_policy: true,
$1  adaptation_policy: true,
$1  energy_policy: true,
$1  description: "Comprehensive climate policy framework"
$1},
$1
$1climate_actions: {
$1  actions: [
$1    {
$1      description: "Energy efficiency retrofits",
$1      type: "Mitigation",
$1      timeline: "2025-2026",
$1      investment: 500000,
$1      expected_impact: "15% reduction in energy use"
$1    },
$1    {
$1      description: "Solar panel installation",
$1      type: "Mitigation",
$1      timeline: "2026-2027",
$1      investment: 1200000,
$1      expected_impact: "30% renewable energy"
$1    },
$1    {
$1      description: "Fleet electrification",
$1      type: "Mitigation",
$1      timeline: "2025-2028",
$1      investment: 800000,
$1      expected_impact: "50% reduction in transport emissions"
$1    }
$1  ],
$1  total_investment: 2500000
$1},
$1
$1targets: {
$1  base_year: 2025,
$1  base_year_emissions: results?.summary?.total_emissions_tons_co2e || 0,
$1  near_term_target: 42,
$1  near_term_year: 2030,
$1  net_zero_year: 2050,
$1  science_based_targets: true,
$1  sbti_validated: false
$1},
$1
`
);

fs.writeFileSync(file, content);
console.log('✅ Added climate_policies, climate_actions, and targets to exportData');

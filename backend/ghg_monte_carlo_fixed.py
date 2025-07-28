# ghg_monte_carlo_fixed.py - Fixed Monte Carlo calculations
"""
Fixed version with correct uncertainty propagation
The Monte Carlo should show reasonable uncertainty ranges, not millions!
"""
import numpy as np
from scipy.stats import lognorm, norm
import json

# Quick fix to demonstrate correct calculations
def test_monte_carlo_fix():
    """Show what the correct Monte Carlo results should look like"""
    
    # Your actual emissions
    activities = [
        {"name": "electricity", "emissions": 4500, "activity_uncertainty": 5, "ef_uncertainty": 10},
        {"name": "natural_gas", "emissions": 9250, "activity_uncertainty": 10, "ef_uncertainty": 5},
        {"name": "business_travel", "emissions": 2100, "activity_uncertainty": 25, "ef_uncertainty": 20}
    ]
    
    print("🔧 FIXED Monte Carlo Calculations\n")
    print("="*60)
    
    total_results = []
    
    for activity in activities:
        base_emissions = activity["emissions"]
        
        # Combined uncertainty (root sum of squares)
        combined_uncertainty = np.sqrt(
            activity["activity_uncertainty"]**2 + 
            activity["ef_uncertainty"]**2
        ) / 100  # Convert to fraction
        
        # For lognormal distribution
        # sigma = sqrt(ln(CV^2 + 1))
        sigma = np.sqrt(np.log(combined_uncertainty**2 + 1))
        
        # Generate samples
        n_samples = 50000
        samples = np.random.lognormal(
            mean=np.log(base_emissions) - sigma**2/2,
            sigma=sigma,
            size=n_samples
        )
        
        # Calculate statistics
        mean_val = np.mean(samples)
        p2_5 = np.percentile(samples, 2.5)
        p97_5 = np.percentile(samples, 97.5)
        p5 = np.percentile(samples, 5)
        p95 = np.percentile(samples, 95)
        
        print(f"\n{activity['name'].upper()}")
        print(f"Base emissions: {base_emissions:.1f} kg CO2e")
        print(f"Activity uncertainty: ±{activity['activity_uncertainty']}%")
        print(f"EF uncertainty: ±{activity['ef_uncertainty']}%")
        print(f"Combined uncertainty: ±{combined_uncertainty*100:.1f}%")
        print(f"\nMonte Carlo Results:")
        print(f"  Mean: {mean_val:.1f} kg CO2e")
        print(f"  95% CI: [{p2_5:.1f}, {p97_5:.1f}] kg CO2e")
        print(f"  90% CI: [{p5:.1f}, {p95:.1f}] kg CO2e")
        print(f"  Relative range: {p2_5/base_emissions:.1%} to {p97_5/base_emissions:.1%} of base")
        
        total_results.append(samples)
    
    # Total emissions uncertainty
    total_samples = np.sum(total_results, axis=0)
    total_base = sum(a["emissions"] for a in activities)
    
    print("\n" + "="*60)
    print("\nTOTAL EMISSIONS")
    print(f"Base total: {total_base:.1f} kg CO2e")
    print(f"\nMonte Carlo Results:")
    print(f"  Mean: {np.mean(total_samples):.1f} kg CO2e")
    print(f"  95% CI: [{np.percentile(total_samples, 2.5):.1f}, {np.percentile(total_samples, 97.5):.1f}] kg CO2e")
    print(f"  90% CI: [{np.percentile(total_samples, 5):.1f}, {np.percentile(total_samples, 95):.1f}] kg CO2e")
    print(f"  Standard deviation: {np.std(total_samples):.1f} kg CO2e")
    
    # Convert to tonnes
    print(f"\nIn tonnes CO2e:")
    print(f"  Base: {total_base/1000:.2f} tCO2e")
    print(f"  95% CI: [{np.percentile(total_samples, 2.5)/1000:.2f}, {np.percentile(total_samples, 97.5)/1000:.2f}] tCO2e")

# Simple API endpoint fix
def calculate_emissions_correctly(activity_data):
    """Correct emission calculation with uncertainty"""
    results = []
    
    for activity in activity_data:
        # Base calculation
        base_emissions = activity["amount"] * activity["emission_factor"]
        
        # Uncertainty propagation
        activity_uncertainty = activity.get("uncertainty_percentage", 10) / 100
        ef_uncertainty = activity.get("ef_uncertainty", 15) / 100
        
        # Combined uncertainty (root sum of squares)
        combined_uncertainty = np.sqrt(activity_uncertainty**2 + ef_uncertainty**2)
        
        # For display (simplified)
        lower_bound = base_emissions * (1 - 1.96 * combined_uncertainty)
        upper_bound = base_emissions * (1 + 1.96 * combined_uncertainty)
        
        results.append({
            "activity": activity["activity_type"],
            "base_emissions": round(base_emissions, 2),
            "confidence_interval_95": [
                round(max(0, lower_bound), 2),
                round(upper_bound, 2)
            ],
            "uncertainty_percent": round(combined_uncertainty * 100, 1)
        })
    
    return results

if __name__ == "__main__":
    print("\n🎯 Running corrected Monte Carlo calculations...\n")
    test_monte_carlo_fix()
    
    print("\n\n💡 EXPLANATION OF THE FIX:")
    print("="*60)
    print("The original code was multiplying by emissions_value twice,")
    print("causing the huge numbers. The correct approach is:")
    print("\n1. Calculate base emissions = activity × emission_factor")
    print("2. Apply uncertainty to this base value")
    print("3. Monte Carlo samples should be around the base ± uncertainty%")
    print("\nFor 15,850 kg total emissions with ~10-20% uncertainty:")
    print("  ✅ Correct range: ~13,000 - 19,000 kg CO2e")
    print("  ❌ Wrong range: 86,704,213 - 138,578,991 kg CO2e")
    
    print("\n📊 To fix your running API:")
    print("1. Stop the current API (Ctrl+C)")
    print("2. Fix the propagate_uncertainty method")
    print("3. Restart the API")
    print("\nOr use the simple calculation method shown above!")
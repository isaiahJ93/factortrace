import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, Area, AreaChart, 
  RadialBarChart, RadialBar, Cell, PieChart, Pie 
} from 'recharts';
import { 
  Activity, Zap, Cloud, Plane, Calculator, TrendingUp, 
  AlertCircle, CheckCircle, Factory, Truck, Droplet, 
  Flame, Snowflake, Package, Building2, Fuel, Trash2, 
  Car, Home, Store, DollarSign, Recycle, ChevronDown, 
  Wind, Download, Upload, FileText, Shield, Paperclip, 
  Battery, Leaf, Euro, Users, Target, BarChart3 
} from 'lucide-react';
import { 
  generatePDFReport, generateBulkPDFReports, 
  usePDFExport, PDFExportData 
} from './pdf-export-handler';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface EliteGHGCalculatorProps {
  companyId?: string;
  companyName?: string;
  reportingPeriod?: string;
  onCalculationComplete?: (data: any) => void;
}

interface DataQualityMetrics {
  dataCompleteness: number;
  evidenceProvided: number;
  dataRecency: number;
  methodologyAccuracy: number;
  overallScore: number;
}

interface EnergyConsumption {
  total_energy_mwh: number;
  electricity_mwh: number;
  heating_cooling_mwh: number;
  steam_mwh: number;
  fuel_combustion_mwh: number;
  renewable_energy_mwh: number;
  renewable_percentage: number;
  energy_intensity_value?: number;
  energy_intensity_unit?: string;
  by_source?: Record<string, number>;
}

interface GHGBreakdown {
  CO2_tonnes: number;
  CH4_tonnes: number;
  N2O_tonnes: number;
  HFCs_tonnes_co2e?: number;
  PFCs_tonnes_co2e?: number;
  SF6_tonnes?: number;
  NF3_tonnes?: number;
  total_co2e: number;
  gwp_version: string;
}

interface InternalCarbonPricing {
  implemented: boolean;
  price_per_tco2e?: number;
  currency: string;
  coverage_scope1: boolean;
  coverage_scope2: boolean;
  coverage_scope3_categories: number[];
  pricing_type?: string;
  total_revenue_generated?: number;
  revenue_allocation?: string;
}

interface ClimatePolicy {
  has_climate_policy: boolean;
  policy_adoption_date?: string;
  policy_document_url?: string;
  policy_description?: string;
  net_zero_target_year?: number;
  interim_targets: Array<{
    year: number;
    reduction_percentage: number;
  }>;
  board_oversight: boolean;
  executive_compensation_linked: boolean;
  covers_value_chain: boolean;
}

interface ClimateActions {
  reporting_year: number;
  capex_climate_eur: number;
  opex_climate_eur: number;
  total_climate_finance_eur: number;
  fte_dedicated: number;
  key_projects: Array<{
    name: string;
    investment_eur: number;
    expected_reduction_tco2e: number;
  }>;
}

interface ESRSE1Data {
  energy_consumption?: EnergyConsumption;
  ghg_breakdown?: GHGBreakdown;
  internal_carbon_pricing?: InternalCarbonPricing;
  climate_policy?: ClimatePolicy;
  climate_actions?: ClimateActions;
}

interface EmissionOption {
  id: string;
  name: string;
  unit: string;
  factor: number;
  source: string;
}

interface EmissionCategory {
  name: string;
  iconType: string;
  options: EmissionOption[];
}

interface EmissionScope {
  name: string;
  description: string;
  color: string;
  categories: Record<string, EmissionCategory>;
}

interface Activity {
  id: number;
  scopeId: string;
  scope: string;
  categoryId: string;
  optionId: string;
  name: string;
  categoryName: string;
  amount: number | string;
  unit: string;
  factor: number;
  source: string;
  uncertainty_percentage: number;
  iconType: string;
}

interface APIResponse {
  summary: {
    total_emissions_tons_co2e: number;
    scope1_emissions: number;
    scope2_location_based: number;
    scope2_market_based: number;
    scope3_emissions: number;
  };
  breakdown: Array<{
    activity_type: string;
    scope: string;
    emissions_kg_co2e: number;
    unit: string;
    calculation_method: string;
  }>;
  reporting_period: string;
  calculation_date: string;
  uncertainty_analysis?: {
    monte_carlo_runs: number;
    mean_emissions?: number;
    std_deviation?: number;
    confidence_interval_95?: number[];
    relative_uncertainty_percent?: number;
  };
  ghg_breakdown?: GHGBreakdown;
  esrs_e1_metadata?: any;
  scope3_breakdown?: Record<string, number>;
}

// ============================================================================
// MODULE-LEVEL CONSTANTS (NO JSX!)
// ============================================================================

const EMISSION_FACTORS = {
  electricity: 0.233,
  natural_gas: 0.185,
  diesel: 2.687,
  petrol: 2.392,
  waste: 0.467,
};

const SCOPE3_CATEGORIES = {
  "1": "Purchased goods and services",
  "2": "Capital goods",
  "3": "Fuel-and-energy-related activities",
  "4": "Upstream transportation and distribution",
  "5": "Waste generated in operations",
  "6": "Business travel",
  "7": "Employee commuting",
  "8": "Upstream leased assets",
  "9": "Downstream transportation and distribution",
  "10": "Processing of sold products",
  "11": "Use of sold products",
  "12": "End-of-life treatment of sold products",
  "13": "Downstream leased assets",
  "14": "Franchises",
  "15": "Investments"
};

const EMISSION_SOURCES = {
  ELECTRICITY: 'electricity',
  NATURAL_GAS: 'natural_gas',
  FLEET: 'fleet',
  WASTE: 'waste',
  TRAVEL: 'travel',
  COMMUTING: 'commuting',
  SUPPLY_CHAIN: 'supply_chain'
};

const DEFAULT_VALUES = {
  REPORTING_YEAR: new Date().getFullYear().toString(),
  CURRENCY: 'EUR',
  LANGUAGE: 'en',
  COUNTRY: 'US'
};

// Define emission scopes without JSX - we'll add icons in the component
const EMISSION_SCOPES_DATA: Record<string, EmissionScope> = {
  scope1: {
    name: "Scope 1 - Direct Emissions",
    description: "Direct GHG emissions from sources owned or controlled by the company",
    color: "red",
    categories: {
      stationary_combustion: {
        name: "Stationary Combustion",
        iconType: "Factory",
        options: [
          { id: "natural_gas_stationary", name: "Natural Gas", unit: "kWh", factor: 0.185, source: "DEFRA 2023" },
          { id: "diesel_stationary", name: "Diesel (Generators/Boilers)", unit: "litres", factor: 2.51, source: "DEFRA 2023" },
          { id: "lpg_stationary", name: "LPG", unit: "litres", factor: 1.56, source: "DEFRA 2023" },
          { id: "coal", name: "Coal", unit: "tonnes", factor: 2419.0, source: "DEFRA 2023" },
          { id: "fuel_oil", name: "Fuel Oil", unit: "litres", factor: 3.18, source: "DEFRA 2023" }
        ]
      },
      mobile_combustion: {
        name: "Mobile Combustion", 
        iconType: "Truck",
        options: [
          { id: "diesel_fleet", name: "Diesel (Company Fleet)", unit: "litres", factor: 2.51, source: "DEFRA 2023" },
          { id: "petrol_fleet", name: "Petrol (Company Fleet)", unit: "litres", factor: 2.19, source: "DEFRA 2023" },
          { id: "van_diesel", name: "Van - Diesel", unit: "km", factor: 0.251, source: "DEFRA 2023" },
          { id: "van_petrol", name: "Van - Petrol", unit: "km", factor: 0.175, source: "DEFRA 2023" },
          { id: "hgv_rigid", name: "HGV - Rigid", unit: "km", factor: 0.811, source: "DEFRA 2023" },
          { id: "hgv_articulated", name: "HGV - Articulated", unit: "km", factor: 0.961, source: "DEFRA 2023" }
        ]
      },
      process_emissions: {
        name: "Process Emissions",
        iconType: "Cloud",
        options: [
          { id: "industrial_process", name: "Industrial Process", unit: "tonnes", factor: 1000.0, source: "Custom" },
          { id: "chemical_production", name: "Chemical Production", unit: "tonnes", factor: 1500.0, source: "IPCC" }
        ]
      },
      fugitive_emissions: {
        name: "Fugitive Emissions",
        iconType: "Wind",
        options: [
          { id: "refrigerant_hfc", name: "Refrigerant Leakage (HFC)", unit: "kg", factor: 1430.0, source: "IPCC AR5" },
          { id: "refrigerant_r410a", name: "R410A Refrigerant", unit: "kg", factor: 2088.0, source: "IPCC AR5" },
          { id: "sf6_leakage", name: "SF6 Leakage", unit: "kg", factor: 22800.0, source: "IPCC AR5" }
        ]
      }
    }
  },
  scope2: {
    name: "Scope 2 - Indirect Emissions (Energy)",
    description: "Indirect GHG emissions from purchased electricity, steam, heating & cooling",
    color: "blue",
    categories: {
      electricity: {
        name: "Purchased Electricity",
        iconType: "Zap",
        options: [
          { id: "electricity_grid", name: "Grid Electricity (Location-based)", unit: "kWh", factor: 0.233, source: "National Grid 2023" },
          { id: "electricity_renewable", name: "100% Renewable (Market-based)", unit: "kWh", factor: 0.0, source: "Supplier Specific" },
          { id: "electricity_partial_green", name: "Partial Renewable Mix", unit: "kWh", factor: 0.116, source: "Supplier Mix" }
        ]
      },
      purchased_heat: {
        name: "Purchased Heat/Steam/Cooling",
        iconType: "Flame",
        options: [
          { id: "district_heating", name: "District Heating", unit: "kWh", factor: 0.210, source: "DEFRA 2023" },
          { id: "purchased_steam", name: "Purchased Steam", unit: "kWh", factor: 0.185, source: "DEFRA 2023" },
          { id: "district_cooling", name: "District Cooling", unit: "kWh", factor: 0.150, source: "DEFRA 2023" }
        ]
      }
    }
  },
  scope3: {
    name: "Scope 3 - Indirect Emissions (Value Chain)",
    description: "All other indirect emissions in the value chain",
    color: "green",
    categories: {
      purchased_goods: {
        name: "1. Purchased Goods & Services",
        iconType: "Package",
        options: [
          { id: "office_paper", name: "Office Paper", unit: "kg", factor: 0.919, source: "DEFRA 2023" },
          { id: "plastic_packaging", name: "Plastic Packaging", unit: "kg", factor: 3.13, source: "DEFRA 2023" },
          { id: "steel_products", name: "Steel Products", unit: "tonnes", factor: 1850.0, source: "DEFRA 2023" },
          { id: "electronics", name: "Electronics", unit: "EUR", factor: 0.39, source: "EPA EEIO (EUR adjusted)" },
          { id: "food_beverages", name: "Food & Beverages", unit: "EUR", factor: 0.35, source: "EPA EEIO (EUR adjusted)" }
        ]
      },
      capital_goods: {
        name: "2. Capital Goods",
        iconType: "Building2",
        options: [
          { id: "machinery", name: "Machinery & Equipment", unit: "EUR", factor: 0.32, source: "EPA EEIO (EUR adjusted)" },
          { id: "buildings", name: "Buildings & Construction", unit: "EUR", factor: 0.26, source: "EPA EEIO (EUR adjusted)" },
          { id: "vehicles", name: "Vehicles", unit: "EUR", factor: 0.37, source: "EPA EEIO (EUR adjusted)" }
        ]
      },
      fuel_energy: {
        name: "3. Fuel & Energy Activities",
        iconType: "Fuel",
        options: [
          { id: "upstream_electricity", name: "Upstream Electricity", unit: "kWh", factor: 0.045, source: "DEFRA 2023" },
          { id: "upstream_natural_gas", name: "Upstream Natural Gas", unit: "kWh", factor: 0.035, source: "DEFRA 2023" },
          { id: "transmission_losses", name: "T&D Losses", unit: "kWh", factor: 0.020, source: "DEFRA 2023" }
        ]
      },
      upstream_transport: {
        name: "4. Upstream Transportation",
        iconType: "Truck",
        options: [
          { id: "road_freight", name: "Road Freight", unit: "tonne.km", factor: 0.096, source: "DEFRA 2023" },
          { id: "rail_freight", name: "Rail Freight", unit: "tonne.km", factor: 0.025, source: "DEFRA 2023" },
          { id: "sea_freight", name: "Sea Freight", unit: "tonne.km", factor: 0.016, source: "DEFRA 2023" },
          { id: "air_freight", name: "Air Freight", unit: "tonne.km", factor: 1.23, source: "DEFRA 2023" }
        ]
      },
      waste: {
        name: "5. Waste Generated",
        iconType: "Trash2",
        options: [
          { id: "waste_landfill", name: "Landfill", unit: "tonnes", factor: 467.0, source: "DEFRA 2023" },
          { id: "waste_recycled", name: "Recycling", unit: "tonnes", factor: 21.0, source: "DEFRA 2023" },
          { id: "waste_composted", name: "Composting", unit: "tonnes", factor: 8.95, source: "DEFRA 2023" },
          { id: "waste_incineration", name: "Incineration", unit: "tonnes", factor: 21.0, source: "DEFRA 2023" },
          { id: "wastewater", name: "Wastewater Treatment", unit: "m3", factor: 0.272, source: "DEFRA 2023" }
        ]
      },
      business_travel: {
        name: "6. Business Travel",
        iconType: "Plane",
        options: [
          { id: "flight_domestic", name: "Domestic Flights", unit: "passenger.km", factor: 0.246, source: "DEFRA 2023" },
          { id: "flight_short_haul", name: "Short Haul Flights", unit: "passenger.km", factor: 0.149, source: "DEFRA 2023" },
          { id: "flight_long_haul", name: "Long Haul Flights", unit: "passenger.km", factor: 0.191, source: "DEFRA 2023" },
          { id: "rail_travel", name: "Rail Travel", unit: "passenger.km", factor: 0.035, source: "DEFRA 2023" },
          { id: "taxi", name: "Taxi/Uber", unit: "km", factor: 0.208, source: "DEFRA 2023" },
          { id: "hotel_stays", name: "Hotel Stays", unit: "nights", factor: 16.1, source: "DEFRA 2023" }
        ]
      },
      employee_commuting: {
        name: "7. Employee Commuting",
        iconType: "Car",
        options: [
          { id: "car_commute", name: "Car (Average)", unit: "km", factor: 0.171, source: "DEFRA 2023" },
          { id: "bus_commute", name: "Bus", unit: "passenger.km", factor: 0.097, source: "DEFRA 2023" },
          { id: "rail_commute", name: "Train/Metro", unit: "passenger.km", factor: 0.035, source: "DEFRA 2023" },
          { id: "bicycle", name: "Bicycle", unit: "km", factor: 0.0, source: "Zero emissions" },
          { id: "remote_work", name: "Remote Work", unit: "days", factor: -8.5, source: "Avoided emissions" }
        ]
      },
      upstream_leased: {
        name: "8. Upstream Leased Assets",
        iconType: "Building2",
        options: [
          { id: "leased_buildings", name: "Leased Buildings Energy", unit: "kWh", factor: 0.233, source: "Grid average" },
          { id: "leased_vehicles", name: "Leased Vehicle Fleet", unit: "km", factor: 0.171, source: "DEFRA 2023" },
          { id: "leased_equipment", name: "Leased Equipment", unit: "hours", factor: 5.5, source: "Estimated" },
          { id: "data_centers", name: "Leased Data Centers", unit: "kWh", factor: 0.233, source: "Grid average" }
        ]
      },
      downstream_transport: {
        name: "9. Downstream Transportation",
        iconType: "Truck",
        options: [
          { id: "product_delivery", name: "Product Delivery", unit: "tonne.km", factor: 0.096, source: "DEFRA 2023" },
          { id: "customer_collection", name: "Customer Collection", unit: "trips", factor: 2.5, source: "Estimated" },
          { id: "third_party_logistics", name: "3PL Distribution", unit: "tonne.km", factor: 0.096, source: "DEFRA 2023" }
        ]
      },
      processing_sold: {
        name: "10. Processing of Sold Products",
        iconType: "Factory",
        options: [
          { id: "intermediate_processing", name: "Intermediate Product Processing", unit: "tonnes", factor: 125.0, source: "Industry average" },
          { id: "customer_manufacturing", name: "Customer Manufacturing", unit: "units", factor: 2.5, source: "LCA estimate" },
          { id: "further_processing", name: "Further Processing", unit: "tonnes", factor: 85.0, source: "Estimated" }
        ]
      },
      use_of_products: {
        name: "11. Use of Sold Products",
        iconType: "Zap",
        options: [
          { id: "product_electricity", name: "Product Energy Use", unit: "kWh", factor: 0.233, source: "Grid average" },
          { id: "product_fuel", name: "Product Fuel Use", unit: "litres", factor: 2.31, source: "DEFRA 2023" },
          { id: "product_lifetime_energy", name: "Product Lifetime Energy", unit: "units", factor: 150.0, source: "LCA estimate" }
        ]
      },
      end_of_life: {
        name: "12. End-of-Life Treatment",
        iconType: "Recycle",
        options: [
          { id: "product_landfill", name: "Products to Landfill", unit: "tonnes", factor: 467.0, source: "DEFRA 2023" },
          { id: "product_recycling", name: "Products Recycled", unit: "tonnes", factor: 21.0, source: "DEFRA 2023" },
          { id: "product_incineration", name: "Products Incinerated", unit: "tonnes", factor: 21.0, source: "DEFRA 2023" }
        ]
      },
      downstream_leased: {
        name: "13. Downstream Leased Assets",
        iconType: "Home",
        options: [
          { id: "leased_real_estate", name: "Leased Real Estate", unit: "m2.year", factor: 55.0, source: "CRREM" },
          { id: "leased_equipment_downstream", name: "Leased Equipment (Customer)", unit: "units.year", factor: 150.0, source: "Estimated" },
          { id: "franchise_buildings", name: "Franchise Buildings", unit: "m2.year", factor: 55.0, source: "CRREM" }
        ]
      },
      franchises: {
        name: "14. Franchises",
        iconType: "Store",
        options: [
          { id: "franchise_energy", name: "Franchise Energy Use", unit: "kWh", factor: 0.233, source: "Grid average" },
          { id: "franchise_operations", name: "Franchise Operations", unit: "locations", factor: 25000.0, source: "Sector average" },
          { id: "franchise_travel", name: "Franchise Business Travel", unit: "EUR", factor: 0.14, source: "EPA EEIO (EUR adjusted)" },
          { id: "franchise_fleet", name: "Franchise Fleet", unit: "km", factor: 0.171, source: "DEFRA 2023" }
        ]
      },
      investments: {
        name: "15. Investments",
        iconType: "DollarSign",
        options: [
          { id: "equity_investments", name: "Equity Investments", unit: "EUR million", factor: 630.0, source: "PCAF (EUR)" },
          { id: "debt_investments", name: "Debt Investments", unit: "EUR million", factor: 325.0, source: "PCAF (EUR)" },
          { id: "project_finance", name: "Project Finance", unit: "EUR million", factor: 415.0, source: "PCAF (EUR)" },
          { id: "investment_funds", name: "Investment Funds", unit: "EUR million", factor: 510.0, source: "PCAF (EUR)" }
        ]
      }
    }
  }
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const EliteGHGCalculator: React.FC<EliteGHGCalculatorProps> = ({
  companyId = 'default',
  companyName = 'Your Company',
  reportingPeriod = new Date().toISOString().slice(0, 7),
  onCalculationComplete 
}) => {
  // State
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isCalculating, setIsCalculating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [monteCarloIterations, setMonteCarloIterations] = useState(10000);
  const [showUncertainty, setShowUncertainty] = useState(true);
  const [expandedScopes, setExpandedScopes] = useState<string[]>(['scope1']);
  const [expandedCategories, setExpandedCategories] = useState<string[]>([]);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [dataQualityScore, setDataQualityScore] = useState<DataQualityMetrics | null>(null);
  const [showESRSE1, setShowESRSE1] = useState(false);
  const [esrsE1Data, setEsrsE1Data] = useState<ESRSE1Data>({});
  const [includeGasBreakdown, setIncludeGasBreakdown] = useState(true);
  const [showBulkExportDialog, setShowBulkExportDialog] = useState(false);
  const [bulkExportProgress, setBulkExportProgress] = useState(0);
  const [isBulkExporting, setIsBulkExporting] = useState(false);
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Icon mapping function
  const getIcon = (iconType: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      Factory: <Factory className="w-5 h-5" />,
      Truck: <Truck className="w-5 h-5" />,
      Cloud: <Cloud className="w-5 h-5" />,
      Wind: <Wind className="w-5 h-5" />,
      Zap: <Zap className="w-5 h-5" />,
      Flame: <Flame className="w-5 h-5" />,
      Package: <Package className="w-5 h-5" />,
      Building2: <Building2 className="w-5 h-5" />,
      Fuel: <Fuel className="w-5 h-5" />,
      Trash2: <Trash2 className="w-5 h-5" />,
      Plane: <Plane className="w-5 h-5" />,
      Car: <Car className="w-5 h-5" />,
      Home: <Home className="w-5 h-5" />,
      Store: <Store className="w-5 h-5" />,
      DollarSign: <DollarSign className="w-5 h-5" />,
      Recycle: <Recycle className="w-5 h-5" />,
    };
    return iconMap[iconType] || <Activity className="w-5 h-5" />;
  };

  // Utility function - showToast inside component
  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
      type === 'success' ? 'bg-green-600' : type === 'error' ? 'bg-red-600' : 'bg-blue-600'
    } text-white max-w-md`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(1rem)';
    setTimeout(() => {
      toast.style.transition = 'all 0.3s ease-out';
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    }, 10);
    
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(1rem)';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  };

  // Effects
  useEffect(() => {
    checkBackendHealth();
  }, []);

  useEffect(() => {
    const score = calculateDataQualityScore();
    setDataQualityScore(score);
  }, [activities]);

  // Methods
  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      setBackendStatus(response.ok ? 'online' : 'offline');
    } catch {
      setBackendStatus('offline');
    }
  };

  const calculateDataQualityScore = (): DataQualityMetrics => {
    if (!activities || activities.length === 0) {
      return {
        dataCompleteness: 0,
        evidenceProvided: 100, // No evidence system, so assume 100%
        dataRecency: 100,
        methodologyAccuracy: 0,
        overallScore: 0
      };
    }
    
    const totalFields = activities.length * 2;
    const filledFields = activities.filter(a => 
      a.amount && parseFloat(String(a.amount)) > 0 && a.unit
    ).length * 2;
    const dataCompleteness = totalFields > 0 ? (filledFields / totalFields) * 100 : 0;
    
    const evidenceProvided = 100; // Since we removed evidence functionality
    
    const currentDate = new Date();
    const reportingDate = new Date(reportingPeriod);
    const monthsDiff = (currentDate.getFullYear() - reportingDate.getFullYear()) * 12 + 
                      (currentDate.getMonth() - reportingDate.getMonth());
    const dataRecency = Math.max(0, 100 - (monthsDiff * 5));
    
    const accurateMethodologies = activities.filter(a => 
      a.source && (a.source.includes('DEFRA') || a.source.includes('EPA') || a.source.includes('IPCC'))
    ).length;
    const methodologyAccuracy = activities.length > 0 ? (accurateMethodologies / activities.length) * 100 : 0;
    
    const overallScore = (
      dataCompleteness * 0.3 +
      evidenceProvided * 0.2 +
      dataRecency * 0.2 +
      methodologyAccuracy * 0.3
    );
    
    return {
      dataCompleteness,
      evidenceProvided,
      dataRecency,
      methodologyAccuracy,
      overallScore
    };
  };

  const preparePDFExportData = () => {
    if (!results) return null;
    
    const safeParseNumber = (value: any): number => {
      if (typeof value === 'number') return value;
      if (typeof value === 'string') return parseFloat(value) || 0;
      return 0;
    };
    
    const calculateScopeFromActivities = (scopeId: string): number => {
      return activities
        .filter(a => a.scopeId === scopeId)
        .reduce((sum, activity) => {
          const amount = safeParseNumber(activity.amount);
          const factor = safeParseNumber(activity.factor);
          return sum + (amount * factor) / 1000;
        }, 0);
    };
    
    const apiSummary = results.summary || {};
    
    const scope1InTons = safeParseNumber(apiSummary.scope1_emissions) / 1000;
    const scope2InTons = safeParseNumber(apiSummary.scope2_location_based) / 1000;
    const scope2MarketInTons = safeParseNumber(apiSummary.scope2_market_based) / 1000;
    const scope3InTons = safeParseNumber(apiSummary.scope3_emissions) / 1000;
    
    const totalEmissions = scope1InTons + scope2InTons + scope3InTons;
    
    const scope1Percentage = totalEmissions > 0 ? (scope1InTons / totalEmissions) * 100 : 0;
    const scope2Percentage = totalEmissions > 0 ? (scope2InTons / totalEmissions) * 100 : 0;
    const scope3Percentage = totalEmissions > 0 ? (scope3InTons / totalEmissions) * 100 : 0;
    
    const breakdown = results.enhancedBreakdown || results.breakdown || [];
    
    const allActivities = [...activities, ...breakdown].filter(Boolean);
    const topEmissionSources = allActivities
      .map(item => {
        const amount = safeParseNumber(item.amount);
        const factor = safeParseNumber(item.factor);
        const emissions = item.emissions_tons || 
                         item.emissions || 
                         (amount * factor / 1000) || 0;
        
        return {
          name: item.name || item.activity || item.category || 'Unknown',
          category: item.categoryName || item.category || item.scope || 'Unknown',
          emissions: emissions,
          percentage: totalEmissions > 0 ? (emissions / totalEmissions) * 100 : 0
        };
      })
      .filter(item => item.emissions > 0)
      .sort((a, b) => b.emissions - a.emissions)
      .slice(0, 5);
    
    const scope3Categories: any = {};
    
    activities
      .filter(a => a.scopeId === 'scope3')
      .forEach(activity => {
        const categoryName = activity.categoryName || 'Other';
        if (!scope3Categories[categoryName]) {
          scope3Categories[categoryName] = {
            category: categoryName,
            emissions: 0,
            activities: 0,
            hasEvidence: false
          };
        }
        
        const amount = safeParseNumber(activity.amount);
        const factor = safeParseNumber(activity.factor);
        const emissions = (amount * factor) / 1000;
        
        scope3Categories[categoryName].emissions += emissions;
        scope3Categories[categoryName].activities += 1;
      });
    
    const scope3Analysis = Object.values(scope3Categories).map((cat: any) => ({
      ...cat,
      percentage: scope3InTons > 0 ? (cat.emissions / scope3InTons) * 100 : 0
    }));
    
    const pdfData = {
      metadata: {
        reportTitle: 'GHG Emissions Report',
        companyName: companyName || 'Company',
        reportingPeriod: reportingPeriod || new Date().getFullYear().toString(),
        generatedDate: new Date().toISOString(),
        documentId: `GHG-${Date.now().toString(36).toUpperCase()}`,
        standard: 'ESRS E1 Compliant',
        methodology: 'GHG Protocol Corporate Standard'
      },
      summary: {
        totalEmissions: totalEmissions,
        scope1: scope1InTons,
        scope2: scope2InTons,
        scope2Market: scope2MarketInTons,
        scope3: scope3InTons,
        scope1Percentage,
        scope2Percentage,
        scope3Percentage,
        dataQualityScore: dataQualityScore?.overallScore || 0,
        evidenceCount: 0
      },
      topEmissionSources,
      scope3Analysis,
      activities: activities.map(a => ({
        ...a,
        emissions: (safeParseNumber(a.amount) * safeParseNumber(a.factor)) / 1000
      })),
      evidenceFiles: [],
      uncertaintyAnalysis: results.uncertainty_analysis || null,
      dataQuality: dataQualityScore || null,
      chartElements: [],
      companyProfile: {
        sector: 'Services',
        employees: 0,
        revenue: 0,
        operations: []
      }
    };
    
    return pdfData;
  };

  const handleExportResults = () => {
    if (!results) {
      showToast('No results to export', 'error');
      return;
    }
    setShowExportDialog(true);
  };

  const handleExportFormat = async (format: 'json' | 'pdf' | 'ixbrl') => {
    setShowExportDialog(false);
    
    try {
      if (format === 'json') {
        exportAsJSON();
      } else if (format === 'pdf') {
        await exportAsPDF();
      } else if (format === 'ixbrl') {
        await exportAsIXBRL();
      }
    } catch (error) {
      console.error(`Export failed for ${format}:`, error);
      showToast(`Failed to export as ${format.toUpperCase()}`, 'error');
    }
  };

  const exportAsJSON = () => {
    const scope3Breakdown = calculateScope3Breakdown();
    
    const exportData = {
      organization: companyName || 'Test Organization',
      lei: "529900HNOAA1KXQJUQ27",
      reporting_period: parseInt(reportingPeriod) || new Date().getFullYear(),
      force_generation: true,
      
      scope1: (results?.summary?.scope1_emissions || 0) / 1000,
      scope2_location: (results?.summary?.scope2_location_based || 0) / 1000,
      scope2_market: (results?.summary?.scope2_market_based || 0) / 1000,
      scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,
      total_emissions: results?.summary?.total_emissions_tons_co2e || 0,
      
      ghg_emissions: {
        lei: "529900HNOAA1KXQJUQ27",
        organization: companyName || "Your Company",
        primary_nace_code: "J.62",
        reporting_period: reportingPeriod,
        scope1: (results?.summary?.scope1_emissions || 0) / 1000,
        scope2_location: (results?.summary?.scope2_location_based || 0) / 1000,
        scope2_market: (results?.summary?.scope2_market_based || 0) / 1000,
        scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,
        total_emissions: results?.summary?.total_emissions_tons_co2e || 0,
        ghg_breakdown: results?.ghg_breakdown || {},
        scope3_breakdown: scope3Breakdown
      },
      
      primary_nace_code: "J.62",
      consolidation_scope: "parent_and_subsidiaries",
      ghg_breakdown: results?.enhancedBreakdown || [],
      scope3_breakdown: scope3Breakdown,
      
      climate_policies: {
        mitigation_policy: true,
        adaptation_policy: true,
        energy_policy: true,
        description: "Comprehensive climate policy framework"
      },
      
      climate_actions: {
        actions: [
          {
            description: "Energy efficiency retrofits",
            type: "Mitigation",
            timeline: "2025-2026",
            investment: 500000,
            expected_impact: "15% reduction in energy use"
          },
          {
            description: "Solar panel installation",
            type: "Mitigation",
            timeline: "2026-2027",
            investment: 1200000,
            expected_impact: "30% renewable energy"
          },
          {
            description: "Fleet electrification",
            type: "Mitigation",
            timeline: "2025-2028",
            investment: 800000,
            expected_impact: "50% reduction in transport emissions"
          }
        ],
        total_investment: 2500000
      },
      
      targets: {
        base_year: 2025,
        base_year_emissions: results?.summary?.total_emissions_tons_co2e || 0,
        near_term_target: 42,
        near_term_year: 2030,
        net_zero_year: 2050,
        science_based_targets: true,
        sbti_validated: false
      },
      
      esrs_e1_data: {
        reporting_year: parseInt(reportingPeriod) || new Date().getFullYear(),
        base_year: 2020,
        target_year: 2030,
        science_based_targets: true,
        net_zero_commitment: true,
        transition_plan_adopted: true,
        ...esrsE1Data
      }
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ghg-emissions-${reportingPeriod}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('JSON export successful', 'success');
  };

  const calculateScope3Breakdown = () => {
    const breakdown: Record<string, number> = {};
    
    // Initialize all categories to 0
    for (let i = 1; i <= 15; i++) {
      breakdown[`category_${i}`] = 0;
    }
    
    // Category mapping from activity type to category number
    const categoryMap: Record<string, number> = {
      // Category 1 - Purchased goods and services
      'office_paper': 1,
      'plastic_packaging': 1,
      'steel_products': 1,
      'electronics': 1,
      'food_beverages': 1,
      
      // Category 2 - Capital goods
      'machinery': 2,
      'buildings': 2,
      'vehicles': 2,
      
      // Category 3 - Fuel-and-energy-related
      'upstream_electricity': 3,
      'upstream_natural_gas': 3,
      'transmission_losses': 3,
      
      // Category 4 - Upstream transportation
      'road_freight': 4,
      'rail_freight': 4,
      'sea_freight': 4,
      'air_freight': 4,
      
      // Category 5 - Waste
      'waste_landfill': 5,
      'waste_recycled': 5,
      'waste_composted': 5,
      'waste_incineration': 5,
      'wastewater': 5,
      
      // Category 6 - Business travel
      'flight_domestic': 6,
      'flight_short_haul': 6,
      'flight_long_haul': 6,
      'rail_travel': 6,
      'taxi': 6,
      'hotel_stays': 6,
      
      // Category 7 - Employee commuting
      'car_commute': 7,
      'bus_commute': 7,
      'rail_commute': 7,
      'bicycle': 7,
      'remote_work': 7,
      
      // Category 8 - Upstream leased assets
      'leased_buildings': 8,
      'leased_vehicles': 8,
      'leased_equipment': 8,
      'data_centers': 8,
      
      // Category 9 - Downstream transportation
      'product_delivery': 9,
      'customer_collection': 9,
      'third_party_logistics': 9,
      
      // Category 10 - Processing of sold products
      'intermediate_processing': 10,
      'customer_manufacturing': 10,
      'further_processing': 10,
      
      // Category 11 - Use of sold products
      'product_electricity': 11,
      'product_fuel': 11,
      'product_lifetime_energy': 11,
      
      // Category 12 - End-of-life treatment
      'product_landfill': 12,
      'product_recycling': 12,
      'product_incineration': 12,
      
      // Category 13 - Downstream leased assets
      'leased_real_estate': 13,
      'leased_equipment_downstream': 13,
      'franchise_buildings': 13,
      
      // Category 14 - Franchises
      'franchise_energy': 14,
      'franchise_operations': 14,
      'franchise_travel': 14,
      'franchise_fleet': 14,
      
      // Category 15 - Investments
      'equity_investments': 15,
      'debt_investments': 15,
      'project_finance': 15,
      'investment_funds': 15
    };
    
    // Calculate emissions for each category from activities
    activities
      .filter(a => a.scopeId === 'scope3')
      .forEach(activity => {
        const categoryNum = categoryMap[activity.optionId];
        if (categoryNum) {
          const amount = parseFloat(String(activity.amount)) || 0;
          const factor = activity.factor || 0;
          const emissions = (amount * factor) / 1000; // Convert to tons
          breakdown[`category_${categoryNum}`] += emissions;
        }
      });
    
    // Also check if results has scope3 breakdown data
    if (results?.scope3_breakdown) {
      Object.entries(results.scope3_breakdown).forEach(([key, value]) => {
        if (key.startsWith('category_') && typeof value === 'number') {
          breakdown[key] = value;
        }
      });
    }
    
    return breakdown;
  };

  const exportAsPDF = async () => {
    showToast('Generating PDF report...', 'info');
    
    try {
      const pdfData = preparePDFExportData();
      
      if (!pdfData) {
        showToast('No data available for PDF export', 'error');
        return;
      }

      const result = await generatePDFReport(pdfData, {
        useBackend: true,
        filename: `GHG_Report_${companyName || 'Company'}_${reportingPeriod}.pdf`,
        compress: true
      });

      if (result.success) {
        showToast(
          `✅ PDF generated successfully! (${(result.size! / 1024).toFixed(1)} KB in ${result.duration?.toFixed(0)}ms)`,
          'success'
        );
      } else {
        throw new Error(result.error || 'PDF generation failed');
      }

      return result;
    } catch (error: any) {
      console.error('PDF export failed:', error);
      showToast(`PDF generation failed: ${error.message}`, 'error');
      return null;
    }
  };

  const exportAsIXBRL = async () => {
    try {
      // Check if user wants strict validation
      const validationLevel = 'standard'; // Temporarily disabled validation dialog

      const exportData = {
        entity_name: esrsE1Data.organizationName || "Demo Organization",
        organization: "Test Organization" || "Demo Organization", 
        lei: "DEMO12345678901234AB" || "DEMO12345678901234",
        reporting_period: parseInt(new Date().getFullYear().toString()) || new Date().getFullYear(),
        validation_level: validationLevel,  // Add validation level
        sector: "Technology" || "Technology",
        primary_nace_code: "J62.01" || "J62.01",
        consolidation_scope: "operational_control" || "operational_control",
        emissions: {
          scope1: parseFloat((results?.totalEmissions?.scope1 || 1000).toString()) || 100,
          scope2_location: parseFloat((results?.totalEmissions?.scope2?.locationBased || 500).toString()) || 50,
          scope2_market: parseFloat((results?.totalEmissions?.scope2?.marketBased || 400).toString()) || 40,
          scope3: parseFloat((results?.totalEmissions?.scope3?.total || 2000).toString()) || 200,
          ghg_breakdown: {
            co2: (parseFloat((results?.totalEmissions?.scope1 || 1000).toString()) || 100) * 0.9,
            ch4: (parseFloat((results?.totalEmissions?.scope1 || 1000).toString()) || 100) * 0.05,
            n2o: (parseFloat((results?.totalEmissions?.scope1 || 1000).toString()) || 100) * 0.05
          }
        }
      };

      console.log("Backend URL:", process.env.REACT_APP_BACKEND_URL);
      console.log("Full URL:", `${process.env.REACT_APP_BACKEND_URL}/esrs-e1/export-ixbrl`);
      const response = await fetch("http://localhost:8000/api/v1/esrs-e1/export-ixbrl", {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData)
      });

      // Check validation results from headers
      const errors = parseInt(response.headers.get('X-Validation-Errors') || '0');
      const warnings = parseInt(response.headers.get('X-Validation-Warnings') || '0');
      const complianceScore = parseFloat(response.headers.get('X-Compliance-Score') || '0');

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `esrs_report_${new Date().toISOString().split('T')[0]}.xhtml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      // Show validation results
      const message = `Export successful!\n\n` +
        `Compliance Score: ${complianceScore}%\n` +
        (errors > 0 ? `\n⚠️ ${errors} compliance errors - fix before regulatory submission` : "") +
        (warnings > 0 ? `\n⚡ ${warnings} warnings - recommended improvements` : "") +
        (errors === 0 && warnings === 0 && complianceScore >= 80 ? "\n✅ Report is fully compliant!" : "");
      
      alert(message);

    } catch (error) {
      console.error('Export failed:', error);
      alert(`Export failed: ${error.message}`);
    }
  };

  const toggleScope = (scopeId: string) => {
    setExpandedScopes(prev => 
      prev.includes(scopeId) 
        ? prev.filter(s => s !== scopeId)
        : [...prev, scopeId]
    );
  };

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => 
      prev.includes(categoryId) 
        ? prev.filter(c => c !== categoryId)
        : [...prev, categoryId]
    );
  };

  const addActivity = (scopeId: string, categoryId: string, optionId: string) => {
    const scope = EMISSION_SCOPES_DATA[scopeId];
    const category = scope.categories[categoryId];
    const option = category.options.find(o => o.id === optionId);
    
    if (option) {
      const newActivity: Activity = {
        id: Date.now(),
        scopeId,
        scope: scopeId.replace('scope', ''),
        categoryId,
        optionId,
        name: option.name,
        categoryName: category.name,
        amount: 0,
        unit: option.unit,
        factor: option.factor,
        source: option.source,
        uncertainty_percentage: 10,
        iconType: category.iconType
      };
      setActivities([...activities, newActivity]);
      showToast(`Added: ${option.name}`, 'success');
    }
  };

  const updateActivity = (id: number, field: string, value: any) => {
    setActivities(prev => prev.map(a => 
      a.id === id ? { ...a, [field]: value } : a
    ));
  };

  const removeActivity = (id: number) => {
    setActivities(prev => prev.filter(a => a.id !== id));
    showToast('Activity removed', 'info');
  };

  const calculateEmissions = async () => {
    if (activities.length === 0) {
      showToast('Please add at least one activity', 'error');
      return;
    }

    const activeActivities = activities.filter(a => parseFloat(String(a.amount)) > 0);
    if (activeActivities.length === 0) {
      showToast('Please enter amounts for your activities', 'error');
      return;
    }

    setIsCalculating(true);
    
    try {
      const emissions_data = activeActivities.map(activity => ({
        activity_type: activity.optionId,
        amount: parseFloat(String(activity.amount)),
        unit: activity.unit,
        uncertainty_percentage: parseFloat(String(activity.uncertainty_percentage)) || 10
      }));

      const response = await fetch(`${API_URL}/api/v1/ghg-calculator/calculate-with-monte-carlo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reporting_period: String(reportingPeriod),
          emissions_data: emissions_data,
          monte_carlo_iterations: monteCarloIterations,
          include_uncertainty: showUncertainty,
          esrs_e1_data: esrsE1Data,
          include_gas_breakdown: includeGasBreakdown
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', response.status, errorText);
        throw new Error(`Calculation failed: ${response.status} ${response.statusText}`);
      }

      const data: APIResponse = await response.json();
      
      const processedResults = processResults(data, activeActivities);
      setResults(processedResults);
      
      if (onCalculationComplete) {
        onCalculationComplete(processedResults);
      }
      
      const totalEmissions = data.summary.total_emissions_tons_co2e;
      let message = `✅ Total: ${totalEmissions.toFixed(2)} tCO₂e`;
      
      if (data.uncertainty_analysis && showUncertainty && data.uncertainty_analysis.confidence_interval_95) {
        const [lower, upper] = data.uncertainty_analysis.confidence_interval_95;
        message += ` (${(lower / 1000).toFixed(2)} - ${(upper / 1000).toFixed(2)} tCO₂e with 95% confidence)`;
      }
      
      showToast(message, 'success');
      
    } catch (error: any) {
      console.error('Calculation failed:', error);
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        showToast('❌ Cannot connect to backend. Please ensure the API is running on port 8000.', 'error');
      } else if (error.message.includes('404')) {
        showToast('❌ API endpoint not found. Check backend configuration.', 'error');
      } else if (error.message.includes('CORS')) {
        showToast('❌ CORS error. Backend needs to allow requests from this origin.', 'error');
      } else {
        showToast(`❌ ${error.message}`, 'error');
      }
    } finally {
      setIsCalculating(false);
    }
  };

  const processResults = (apiData: APIResponse, activeActivities: Activity[]) => {
    const summary = apiData.summary;
    
    const backendToFrontend: Record<string, string> = {
      'electricity': 'electricity_grid',
      'natural gas': 'natural_gas_stationary',
      'diesel': 'diesel_fleet',
      'gasoline': 'petrol_fleet'
    };
    
    const activityMap = new Map<string, Activity>();
    activeActivities.forEach(a => {
      activityMap.set(a.optionId, a);
    });
    
    const enhancedBreakdown = apiData.breakdown.map((item) => {
      const frontendActivityType = backendToFrontend[item.activity_type] || item.activity_type;
      const activity = activityMap.get(frontendActivityType) || 
                      Array.from(activityMap.values()).find(a => 
                        a.name.toLowerCase().includes(item.activity_type.toLowerCase())
                      );
      
      return {
        ...item,
        ...activity,
        frontendActivityType,
        emissions_tons: item.emissions_kg_co2e / 1000,
        emissions_kg_co2e: item.emissions_kg_co2e,
        categoryName: activity?.categoryName || item.activity_type,
        name: activity?.name || item.activity_type,
        iconType: activity?.iconType || 'Activity'
      };
    });
    
    const categoryTotals = enhancedBreakdown.reduce((acc: any, item: any) => {
      const key = item.categoryName || item.activity_type;
      
      if (!acc[key]) {
        acc[key] = {
          category: key,
          categoryName: key,
          activity_type: item.activity_type,
          scope: item.scope,
          emissions: 0,
          emissions_kg_co2e: 0,
          items: [],
          iconType: item.iconType
        };
      }
      
      acc[key].emissions += item.emissions_tons;
      acc[key].emissions_kg_co2e += item.emissions_kg_co2e;
      acc[key].items.push(item);
      
      return acc;
    }, {});
    
    const metadata = {
      calculation_date: apiData.calculation_date,
      reporting_period: apiData.reporting_period,
      monte_carlo_iterations: apiData.uncertainty_analysis?.monte_carlo_runs || 0,
      total_activities: activeActivities.length,
      data_quality_score: dataQualityScore,
      has_esrs_e1_data: !!esrsE1Data && Object.keys(esrsE1Data).length > 0
    };
    
    // Add scope3_breakdown to results if it exists
    const scope3Breakdown = calculateScope3Breakdown();
    
    return {
      ...apiData,
      enhancedBreakdown,
      categoryTotals: Object.values(categoryTotals).sort((a: any, b: any) => b.emissions - a.emissions),
      chartData: prepareChartData(summary, categoryTotals),
      metadata,
      ghg_breakdown: apiData.ghg_breakdown,
      esrs_e1_metadata: apiData.esrs_e1_metadata,
      scope3_breakdown: scope3Breakdown
    };
  };

  const prepareChartData = (summary: any, categoryTotals: any) => {
    const scopeData = [
      { name: 'Scope 1', value: summary.scope1_emissions / 1000, fill: '#ef4444' },
      { name: 'Scope 2', value: summary.scope2_location_based / 1000, fill: '#3b82f6' },
      { name: 'Scope 3', value: summary.scope3_emissions / 1000, fill: '#10b981' }
    ].filter(item => item.value > 0);
    
    const topCategories = Object.values(categoryTotals || {})
      .filter((cat: any) => cat && cat.emissions > 0)
      .sort((a: any, b: any) => b.emissions - a.emissions)
      .slice(0, 10)
      .map((cat: any) => ({
        name: cat.category && cat.category.length > 20 
          ? cat.category.substring(0, 20) + '...' 
          : (cat.category || 'Unknown'),
        emissions: cat.emissions || 0,
        scope: cat.scope || 'unknown'
      }));
    
    return { scopeData, topCategories };
  };

  // Sub-components
  const DataQualityIndicator = () => {
    if (!dataQualityScore) return null;
    
    const getScoreColor = (value: number) => {
      if (value >= 80) return 'text-green-500';
      if (value >= 60) return 'text-yellow-500';
      return 'text-red-500';
    };
    
    const getScoreLabel = (value: number) => {
      if (value >= 80) return 'Excellent';
      if (value >= 60) return 'Good';
      if (value >= 40) return 'Fair';
      return 'Needs Improvement';
    };
    
    return (
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          <Shield className="w-5 h-5 mr-2 text-blue-500" />
          Data Quality Score
        </h3>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className={`text-3xl font-bold ${getScoreColor(dataQualityScore.overallScore)}`}>
              {dataQualityScore.overallScore.toFixed(0)}%
            </span>
            <span className={`text-sm ${getScoreColor(dataQualityScore.overallScore)}`}>
              {getScoreLabel(dataQualityScore.overallScore)}
            </span>
          </div>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Data Completeness</span>
              <span className={getScoreColor(dataQualityScore.dataCompleteness)}>
                {dataQualityScore.dataCompleteness.toFixed(0)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Data Recency</span>
              <span className={getScoreColor(dataQualityScore.dataRecency)}>
                {dataQualityScore.dataRecency.toFixed(0)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Methodology Accuracy</span>
              <span className={getScoreColor(dataQualityScore.methodologyAccuracy)}>
                {dataQualityScore.methodologyAccuracy.toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const ExportDialog = () => {
    if (!showExportDialog) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
          <h3 className="text-xl font-bold mb-4 text-white">Select Export Format</h3>
          <div className="space-y-3">
            <button
              onClick={() => handleExportFormat('json')}
              className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center justify-between transition-colors"
            >
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5" />
                <span className="font-medium">JSON Data Export</span>
              </div>
              <span className="text-sm text-blue-200">Machine-readable</span>
            </button>
            <button
              onClick={() => handleExportFormat('pdf')}
              className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center justify-between transition-colors"
            >
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5" />
                <span className="font-medium">PDF Report</span>
              </div>
              <span className="text-sm text-green-200">Professional multi-page</span>
            </button>
            <button
              onClick={() => handleExportFormat('ixbrl')}
              className="w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg flex items-center justify-between transition-colors"
            >
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5" />
                <span className="font-medium">iXBRL Filing</span>
              </div>
              <span className="text-sm text-purple-200">Regulatory compliance</span>
            </button>
          </div>
          <button
            onClick={() => setShowExportDialog(false)}
            className="mt-4 w-full px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  };

  const ESRSE1DataCollection: React.FC<{
    esrsData: ESRSE1Data;
    onDataChange: (data: ESRSE1Data) => void;
    reportingPeriod: string;
  }> = ({ esrsData, onDataChange, reportingPeriod }) => {
    const [activeTab, setActiveTab] = useState<'energy' | 'carbon' | 'policy' | 'actions'>('energy');

    const updateData = (section: keyof ESRSE1Data, data: any) => {
      onDataChange({
        ...esrsData,
        [section]: data
      });
    };

    return (
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">ESRS E1 Compliance Data</h3>
        
        <div className="flex space-x-2 mb-6 border-b border-gray-700">
          <button
            onClick={() => setActiveTab('energy')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'energy' 
                ? 'text-blue-400 border-blue-400' 
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Battery className="w-4 h-4" />
              E1-5: Energy
            </div>
          </button>
          <button
            onClick={() => setActiveTab('carbon')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'carbon' 
                ? 'text-blue-400 border-blue-400' 
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Euro className="w-4 h-4" />
              E1-8: Carbon Pricing
            </div>
          </button>
          <button
            onClick={() => setActiveTab('policy')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'policy' 
                ? 'text-blue-400 border-blue-400' 
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              E1-2: Climate Policy
            </div>
          </button>
          <button
            onClick={() => setActiveTab('actions')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'actions' 
                ? 'text-blue-400 border-blue-400' 
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              E1-3: Actions & Resources
            </div>
          </button>
        </div>

        {activeTab === 'energy' && (
          <div className="space-y-4">
            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Energy Consumption (MWh)</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-400">Electricity</label>
                  <input
                    type="number"
                    value={esrsData.energy_consumption?.electricity_mwh || 0}
                    onChange={(e) => updateData('energy_consumption', {
                      ...esrsData.energy_consumption,
                      electricity_mwh: parseFloat(e.target.value) || 0
                    })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Heating & Cooling</label>
                  <input
                    type="number"
                    value={esrsData.energy_consumption?.heating_cooling_mwh || 0}
                    onChange={(e) => updateData('energy_consumption', {
                      ...esrsData.energy_consumption,
                      heating_cooling_mwh: parseFloat(e.target.value) || 0
                    })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Steam</label>
                  <input
                    type="number"
                    value={esrsData.energy_consumption?.steam_mwh || 0}
                    onChange={(e) => updateData('energy_consumption', {
                      ...esrsData.energy_consumption,
                      steam_mwh: parseFloat(e.target.value) || 0
                    })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Fuel Combustion</label>
                  <input
                    type="number"
                    value={esrsData.energy_consumption?.fuel_combustion_mwh || 0}
                    onChange={(e) => updateData('energy_consumption', {
                      ...esrsData.energy_consumption,
                      fuel_combustion_mwh: parseFloat(e.target.value) || 0
                    })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Renewable Energy</label>
                  <input
                    type="number"
                    value={esrsData.energy_consumption?.renewable_energy_mwh || 0}
                    onChange={(e) => updateData('energy_consumption', {
                      ...esrsData.energy_consumption,
                      renewable_energy_mwh: parseFloat(e.target.value) || 0
                    })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Energy Intensity</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      value={esrsData.energy_consumption?.energy_intensity_value || 0}
                      onChange={(e) => updateData('energy_consumption', {
                        ...esrsData.energy_consumption,
                        energy_intensity_value: parseFloat(e.target.value) || 0
                      })}
                      className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                      placeholder="0"
                    />
                    <select
                      value={esrsData.energy_consumption?.energy_intensity_unit || 'MWh/million_EUR'}
                      onChange={(e) => updateData('energy_consumption', {
                        ...esrsData.energy_consumption,
                        energy_intensity_unit: e.target.value
                      })}
                      className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    >
                      <option value="MWh/million_EUR">MWh/M€</option>
                      <option value="MWh/employee">MWh/employee</option>
                      <option value="MWh/m2">MWh/m²</option>
                    </select>
                  </div>
                </div>
              </div>
              
              {esrsData.energy_consumption && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Total Energy Consumption:</span>
                    <span className="text-gray-200 font-medium">
                      {((esrsData.energy_consumption.electricity_mwh || 0) +
                       (esrsData.energy_consumption.heating_cooling_mwh || 0) +
                       (esrsData.energy_consumption.steam_mwh || 0) +
                       (esrsData.energy_consumption.fuel_combustion_mwh || 0)).toFixed(2)} MWh
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mt-2">
                    <span className="text-gray-400">Renewable Percentage:</span>
                    <span className="text-green-400 font-medium">
                      {esrsData.energy_consumption.total_energy_mwh > 0
                        ? ((esrsData.energy_consumption.renewable_energy_mwh / esrsData.energy_consumption.total_energy_mwh) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'carbon' && (
          <div className="space-y-4">
            <div className="bg-gray-900 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-300">Internal Carbon Pricing</h4>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={esrsData.internal_carbon_pricing?.implemented || false}
                    onChange={(e) => updateData('internal_carbon_pricing', {
                      ...esrsData.internal_carbon_pricing,
                      implemented: e.target.checked
                    })}
                    className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mr-2"
                  />
                  <span className="text-sm text-gray-400">Implemented</span>
                </label>
              </div>
              
              {esrsData.internal_carbon_pricing?.implemented && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs text-gray-400">Price per tCO₂e</label>
                      <input
                        type="number"
                        value={esrsData.internal_carbon_pricing?.price_per_tco2e || 0}
                        onChange={(e) => updateData('internal_carbon_pricing', {
                          ...esrsData.internal_carbon_pricing,
                          price_per_tco2e: parseFloat(e.target.value) || 0
                        })}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                        placeholder="0"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400">Currency</label>
                      <select
                        value={esrsData.internal_carbon_pricing?.currency || 'EUR'}
                        onChange={(e) => updateData('internal_carbon_pricing', {
                          ...esrsData.internal_carbon_pricing,
                          currency: e.target.value
                        })}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                      >
                        <option value="EUR">EUR</option>
                        <option value="USD">USD</option>
                        <option value="GBP">GBP</option>
                      </select>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-xs text-gray-400 mb-2 block">Scope Coverage</label>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={esrsData.internal_carbon_pricing?.coverage_scope1 || false}
                          onChange={(e) => updateData('internal_carbon_pricing', {
                            ...esrsData.internal_carbon_pricing,
                            coverage_scope1: e.target.checked
                          })}
                          className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mr-2"
                        />
                        <span className="text-sm text-gray-300">Scope 1 emissions</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={esrsData.internal_carbon_pricing?.coverage_scope2 || false}
                          onChange={(e) => updateData('internal_carbon_pricing', {
                            ...esrsData.internal_carbon_pricing,
                            coverage_scope2: e.target.checked
                          })}
                          className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mr-2"
                        />
                        <span className="text-sm text-gray-300">Scope 2 emissions</span>
                      </label>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-xs text-gray-400">Pricing Type</label>
                    <select
                      value={esrsData.internal_carbon_pricing?.pricing_type || 'shadow'}
                      onChange={(e) => updateData('internal_carbon_pricing', {
                        ...esrsData.internal_carbon_pricing,
                        pricing_type: e.target.value
                      })}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    >
                      <option value="shadow">Shadow Price</option>
                      <option value="internal">Internal Fee</option>
                      <option value="implicit">Implicit Price</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'policy' && (
          <div className="space-y-4">
            <div className="bg-gray-900 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-300">Climate Change Policy</h4>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={esrsData.climate_policy?.has_climate_policy || false}
                    onChange={(e) => updateData('climate_policy', {
                      ...esrsData.climate_policy,
                      has_climate_policy: e.target.checked
                    })}
                    className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mr-2"
                  />
                  <span className="text-sm text-gray-400">Has Policy</span>
                </label>
              </div>
              
              {esrsData.climate_policy?.has_climate_policy && (
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-gray-400">Policy Adoption Date</label>
                    <input
                      type="date"
                      value={esrsData.climate_policy?.policy_adoption_date || ''}
                      onChange={(e) => updateData('climate_policy', {
                        ...esrsData.climate_policy,
                        policy_adoption_date: e.target.value
                      })}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    />
                  </div>
                  
                  <div>
                    <label className="text-xs text-gray-400">Net Zero Target Year</label>
                    <input
                      type="number"
                      value={esrsData.climate_policy?.net_zero_target_year || 2050}
                      onChange={(e) => updateData('climate_policy', {
                        ...esrsData.climate_policy,
                        net_zero_target_year: parseInt(e.target.value) || 2050
                      })}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                      min="2025"
                      max="2100"
                    />
                  </div>
                  
                  <div>
                    <label className="text-xs text-gray-400">Policy Document URL</label>
                    <input
                      type="url"
                      value={esrsData.climate_policy?.policy_document_url || ''}
                      onChange={(e) => updateData('climate_policy', {
                        ...esrsData.climate_policy,
                        policy_document_url: e.target.value
                      })}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                      placeholder="https://..."
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={esrsData.climate_policy?.board_oversight || false}
                        onChange={(e) => updateData('climate_policy', {
                          ...esrsData.climate_policy,
                          board_oversight: e.target.checked
                        })}
                        className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mr-2"
                      />
                      <span className="text-sm text-gray-300">Board-level oversight</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={esrsData.climate_policy?.executive_compensation_linked || false}
                        onChange={(e) => updateData('climate_policy', {
                          ...esrsData.climate_policy,
                          executive_compensation_linked: e.target.checked
                        })}
                        className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mr-2"
                      />
                      <span className="text-sm text-gray-300">Executive compensation linked to climate targets</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={esrsData.climate_policy?.covers_value_chain || false}
                        onChange={(e) => updateData('climate_policy', {
                          ...esrsData.climate_policy,
                          covers_value_chain: e.target.checked
                        })}
                        className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 mr-2"
                      />
                      <span className="text-sm text-gray-300">Covers entire value chain</span>
                    </label>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="space-y-4">
            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Climate Actions and Resources</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-400">CapEx Climate (EUR)</label>
                  <input
                    type="number"
                    value={esrsData.climate_actions?.capex_climate_eur || 0}
                    onChange={(e) => updateData('climate_actions', {
                      ...esrsData.climate_actions,
                      capex_climate_eur: parseFloat(e.target.value) || 0,
                      reporting_year: new Date(reportingPeriod).getFullYear()
                    })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">OpEx Climate (EUR)</label>
                  <input
                    type="number"
                    value={esrsData.climate_actions?.opex_climate_eur || 0}
                    onChange={(e) => updateData('climate_actions', {
                      ...esrsData.climate_actions,
                      opex_climate_eur: parseFloat(e.target.value) || 0,
                      reporting_year: new Date(reportingPeriod).getFullYear()
                    })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">FTEs Dedicated</label>
                  <input
                    type="number"
                    value={esrsData.climate_actions?.fte_dedicated || 0}
                    onChange={(e) => updateData('climate_actions', {
                      ...esrsData.climate_actions,
                      fte_dedicated: parseFloat(e.target.value) || 0,
                      reporting_year: new Date(reportingPeriod).getFullYear()
                    })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200"
                    placeholder="0"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Total Climate Finance</label>
                  <div className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-gray-300">
                    €{((esrsData.climate_actions?.capex_climate_eur || 0) + 
                       (esrsData.climate_actions?.opex_climate_eur || 0)).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Return JSX
  return (
    <div className="w-full space-y-6 p-6 bg-gray-900 min-h-screen">
      {/* Header with Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-light text-gray-100 mb-2">
              Elite GHG Emissions Calculator
            </h2>
            <p className="text-gray-400">
              Complete GHG Protocol coverage with Monte Carlo uncertainty analysis
            </p>
          </div>
          <div className="flex items-center gap-4">
            {dataQualityScore && (
              <div className="flex items-center gap-2">
                <Shield className={`w-5 h-5 ${
                  dataQualityScore.overallScore >= 80 ? 'text-green-500' :
                  dataQualityScore.overallScore >= 60 ? 'text-yellow-500' : 'text-red-500'
                }`} />
                <span className="text-sm text-gray-400">
                  Quality: {dataQualityScore.overallScore.toFixed(0)}%
                </span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full animate-pulse ${
                backendStatus === 'online' ? 'bg-green-500' : 
                backendStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
              }`} />
              <span className="text-sm text-gray-400">
                Backend {backendStatus}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Data Quality Score Display */}
      {activities.length > 0 && <DataQualityIndicator />}

      {/* Monte Carlo Settings and ESRS E1 Toggle */}
      <div className="bg-gray-800 rounded-lg p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showUncertainty}
              onChange={(e) => setShowUncertainty(e.target.checked)}
              className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-300">Include Uncertainty Analysis</span>
          </label>
          {showUncertainty && (
            <select
              value={monteCarloIterations}
              onChange={(e) => setMonteCarloIterations(parseInt(e.target.value))}
              className="px-3 py-1 bg-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1000">1,000 iterations (fast)</option>
              <option value="10000">10,000 iterations (balanced)</option>
              <option value="50000">50,000 iterations (accurate)</option>
            </select>
          )}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeGasBreakdown}
              onChange={(e) => setIncludeGasBreakdown(e.target.checked)}
              className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-300">GHG Gas Breakdown</span>
          </label>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowESRSE1(!showESRSE1)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              showESRSE1 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              ESRS E1 Data
            </div>
          </button>
          <span className="text-xs text-gray-500">
            Reporting Period: {reportingPeriod}
          </span>
        </div>
      </div>

      {/* ESRS E1 Data Collection */}
      {showESRSE1 && (
        <ESRSE1DataCollection
          esrsData={esrsE1Data}
          onDataChange={setEsrsE1Data}
          reportingPeriod={reportingPeriod}
        />
      )}

      {/* Activity Counter */}
      {activities.length > 0 && (
        <div className="bg-blue-900/20 border border-blue-600/30 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-blue-400" />
            <span className="text-blue-300">
              {activities.length} activities added • {activities.filter(a => parseFloat(String(a.amount)) > 0).length} with values
            </span>
          </div>
          <button
            onClick={() => {
              setActivities([]);
              showToast('All activities cleared', 'info');
            }}
            className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Scopes */}
      <div className="space-y-4">
        {Object.entries(EMISSION_SCOPES_DATA).map(([scopeId, scope]) => (
          <div key={scopeId} className="bg-gray-800 rounded-lg overflow-hidden">
            {/* Scope Header */}
            <button
              onClick={() => toggleScope(scopeId)}
              className={`w-full px-6 py-4 flex items-center justify-between hover:bg-gray-750 transition-colors border-l-4 ${
                scopeId === 'scope1' ? 'border-red-500' :
                scopeId === 'scope2' ? 'border-blue-500' : 'border-green-500'
              }`}
            >
              <div className="text-left">
                <h3 className="font-medium text-lg text-gray-100">{scope.name}</h3>
                <p className="text-sm text-gray-400">{scope.description}</p>
              </div>
              <ChevronDown className={`w-6 h-6 text-gray-400 transition-transform ${
                expandedScopes.includes(scopeId) ? 'rotate-180' : ''
              }`} />
            </button>

            {/* Categories within Scope */}
            {expandedScopes.includes(scopeId) && (
              <div className="p-4 space-y-3 bg-gray-850">
                {Object.entries(scope.categories).map(([categoryId, category]) => (
                  <div key={categoryId} className="bg-gray-900 rounded-lg">
                    {/* Category Header */}
                    <button
                      onClick={() => toggleCategory(`${scopeId}_${categoryId}`)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-800 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center">
                          {getIcon(category.iconType)}
                        </div>
                        <span className="font-medium text-gray-200">{category.name}</span>
                      </div>
                      <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${
                        expandedCategories.includes(`${scopeId}_${categoryId}`) ? 'rotate-180' : ''
                      }`} />
                    </button>

                    {/* Options */}
                    {expandedCategories.includes(`${scopeId}_${categoryId}`) && (
                      <div className="px-4 pb-3 space-y-2">
                        {category.options.map(option => (
                          <button
                            key={option.id}
                            onClick={() => addActivity(scopeId, categoryId, option.id)}
                            className="w-full text-left px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded transition-colors group"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-medium text-gray-200">{option.name}</p>
                                <p className="text-xs text-gray-400">
                                  {option.factor} kg CO₂e/{option.unit} • {option.source}
                                </p>
                              </div>
                              <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                                Add +
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Active Activities */}
      {activities.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-100 mb-4">Active Activities</h3>
          
          {/* Group by scope */}
          {['scope1', 'scope2', 'scope3'].map(scopeId => {
            const scopeActivities = activities.filter(a => a.scopeId === scopeId);
            if (scopeActivities.length === 0) return null;
            
            const scope = EMISSION_SCOPES_DATA[scopeId];
            
            return (
              <div key={scopeId} className="mb-6">
                <h4 className="text-sm font-medium text-gray-400 mb-3">{scope.name}</h4>
                <div className="space-y-2">
                  {scopeActivities.map(activity => (
                    <div key={activity.id} className="flex items-center gap-3 p-3 bg-gray-900 rounded-lg">
                      <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
                        {getIcon(activity.iconType)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-200">{activity.name}</p>
                        <p className="text-xs text-gray-500">{activity.categoryName} • {activity.source}</p>
                      </div>
                      <input
                        type="number"
                        value={activity.amount}
                        onChange={(e) => updateActivity(activity.id, 'amount', e.target.value)}
                        className="w-32 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="0"
                        min="0"
                        step="any"
                      />
                      <span className="text-sm text-gray-400 w-20">{activity.unit}</span>
                      {showUncertainty && (
                        <>
                          <input
                            type="number"
                            value={activity.uncertainty_percentage}
                            onChange={(e) => updateActivity(activity.id, 'uncertainty_percentage', e.target.value)}
                            className="w-16 px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="10"
                            title="Uncertainty %"
                            min="0"
                            max="100"
                          />
                          <span className="text-xs text-gray-500">%</span>
                        </>
                      )}
                      <button
                        onClick={() => removeActivity(activity.id)}
                        className="text-red-400 hover:text-red-300 transition-colors text-xl leading-none p-1"
                        title="Remove activity"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Calculate Button */}
      <button
        onClick={calculateEmissions}
        disabled={isCalculating || activities.length === 0 || backendStatus === 'offline'}
        className="w-full px-6 py-4 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 transition-all duration-300 font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
      >
        <Calculator className="w-5 h-5" />
        {isCalculating ? 'Calculating...' : 'Calculate Emissions'}
      </button>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-red-600/20 to-red-700/20 border border-red-600/30 rounded-lg p-6">
              <h4 className="text-sm text-red-400 mb-2">Scope 1 - Direct</h4>
              <p className="text-3xl font-light text-white">{(results.summary.scope1_emissions / 1000).toFixed(2)}</p>
              <p className="text-sm text-red-300 mt-1">tCO₂e</p>
            </div>
            <div className="bg-gradient-to-br from-blue-600/20 to-blue-700/20 border border-blue-600/30 rounded-lg p-6">
              <h4 className="text-sm text-blue-400 mb-2">Scope 2 - Energy</h4>
              <p className="text-3xl font-light text-white">{(results.summary.scope2_location_based / 1000).toFixed(2)}</p>
              <p className="text-sm text-blue-300 mt-1">tCO₂e</p>
              {results.summary.scope2_market_based !== results.summary.scope2_location_based && (
                <p className="text-xs text-blue-400 mt-2">
                  Market: {(results.summary.scope2_market_based / 1000).toFixed(2)} tCO₂e
                </p>
              )}
            </div>
            <div className="bg-gradient-to-br from-green-600/20 to-green-700/20 border border-green-600/30 rounded-lg p-6">
              <h4 className="text-sm text-green-400 mb-2">Scope 3 - Value Chain</h4>
              <p className="text-3xl font-light text-white">{(results.summary.scope3_emissions / 1000).toFixed(2)}</p>
              <p className="text-sm text-green-300 mt-1">tCO₂e</p>
            </div>
            <div className="bg-gradient-to-br from-purple-600/20 to-purple-700/20 border border-purple-600/30 rounded-lg p-6">
              <h4 className="text-sm text-purple-400 mb-2">Total Emissions</h4>
              <p className="text-3xl font-light text-white">{results.summary.total_emissions_tons_co2e.toFixed(2)}</p>
              <p className="text-sm text-purple-300 mt-1">tCO₂e</p>
              {results.uncertainty_analysis && results.uncertainty_analysis.relative_uncertainty_percent && (
                <p className="text-xs text-purple-400 mt-2">
                  ±{results.uncertainty_analysis.relative_uncertainty_percent.toFixed(1)}%
                </p>
              )}
            </div>
          </div>

          {/* GHG Gas Breakdown */}
          {results.ghg_breakdown && includeGasBreakdown && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-100 mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2 text-green-500" />
                GHG Breakdown by Gas Type
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm text-gray-400 mb-3">Individual Gases</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-3 bg-gray-900 rounded">
                      <span className="text-gray-300">CO₂ (Carbon Dioxide)</span>
                      <span className="text-gray-100 font-medium">{results.ghg_breakdown.CO2_tonnes.toFixed(2)} tonnes</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-gray-900 rounded">
                      <span className="text-gray-300">CH₄ (Methane)</span>
                      <span className="text-gray-100 font-medium">{results.ghg_breakdown.CH4_tonnes.toFixed(3)} tonnes</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-gray-900 rounded">
                      <span className="text-gray-300">N₂O (Nitrous Oxide)</span>
                      <span className="text-gray-100 font-medium">{results.ghg_breakdown.N2O_tonnes.toFixed(3)} tonnes</span>
                    </div>
                    {results.ghg_breakdown.HFCs_tonnes_co2e > 0 && (
                      <div className="flex justify-between items-center p-3 bg-gray-900 rounded">
                        <span className="text-gray-300">HFCs</span>
                        <span className="text-gray-100 font-medium">{results.ghg_breakdown.HFCs_tonnes_co2e.toFixed(3)} tCO₂e</span>
                      </div>
                    )}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm text-gray-400 mb-3">Summary</h4>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-300">Total CO₂ Equivalent</span>
                      <span className="text-xl font-medium text-gray-100">{results.ghg_breakdown.total_co2e.toFixed(2)} tCO₂e</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-400">GWP Version</span>
                      <span className="text-gray-300">{results.ghg_breakdown.gwp_version}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Uncertainty Analysis */}
          {results.uncertainty_analysis && showUncertainty && results.uncertainty_analysis.confidence_interval_95 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-100 mb-4">Uncertainty Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm text-gray-400 mb-2">95% Confidence Interval</h4>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Lower Bound</span>
                      <span className="text-gray-100 font-medium">
                        {(results.uncertainty_analysis.confidence_interval_95[0] / 1000).toFixed(2)} tCO₂e
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-gray-300">Upper Bound</span>
                      <span className="text-gray-100 font-medium">
                        {(results.uncertainty_analysis.confidence_interval_95[1] / 1000).toFixed(2)} tCO₂e
                      </span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm text-gray-400 mb-2">Statistical Measures</h4>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Mean</span>
                      <span className="text-gray-100 font-medium">
                        {((results.uncertainty_analysis.mean_emissions || 0) / 1000).toFixed(2)} tCO₂e
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-gray-300">Standard Deviation</span>
                      <span className="text-gray-100 font-medium">
                        {((results.uncertainty_analysis.std_deviation || 0) / 1000).toFixed(2)} tCO₂e
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Visualizations */}
          {results.chartData && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Scope Breakdown Pie Chart */}
              {results.chartData.scopeData.length > 0 && (
                <div className="bg-gray-800 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-100 mb-4">Emissions by Scope</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={results.chartData.scopeData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {results.chartData.scopeData.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value: any) => `${value.toFixed(2)} tCO₂e`}
                        contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '0.5rem' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Top Categories Bar Chart */}
              {results.chartData.topCategories.length > 0 && (
                <div className="bg-gray-800 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-100 mb-4">Top Emission Categories</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={results.chartData.topCategories} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} tick={{ fill: '#9ca3af' }} />
                      <YAxis tick={{ fill: '#9ca3af' }} />
                      <Tooltip 
                        formatter={(value: any) => `${value.toFixed(3)} tCO₂e`}
                        contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '0.5rem' }}
                        labelStyle={{ color: '#d1d5db' }}
                      />
                      <Bar dataKey="emissions" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* Category Breakdown */}
          {results.categoryTotals && results.categoryTotals.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-100">Emissions by Category</h3>
                <button
                  onClick={handleExportResults}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  <Download className="w-4 h-4" />
                  <span className="text-sm">Export Results</span>
                </button>
              </div>
              <div className="space-y-3">
                {results.categoryTotals.map((category: any, idx: number) => (
                  <div key={idx} className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center">
                          {getIcon(category.iconType || 'Activity')}
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-200">{category.category}</span>
                          <span className="text-xs text-gray-500 ml-2">Scope {category.scope.replace('scope_', '')}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-100">{category.emissions.toFixed(3)} tCO₂e</p>
                        <p className="text-xs text-gray-500">
                          {((category.emissions / results.summary.total_emissions_tons_co2e) * 100).toFixed(1)}% of total
                        </p>
                      </div>
                    </div>
                    <div className="text-xs text-gray-400">
                      {category.items.map((item: any) => item.name).join(' • ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scope 3 Breakdown */}
          {results.scope3_breakdown && Object.keys(results.scope3_breakdown).length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-100 mb-4">Scope 3 Category Breakdown</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(results.scope3_breakdown)
                  .filter(([_, value]) => value > 0)
                  .sort((a, b) => (b[1] as number) - (a[1] as number))
                  .map(([category, emissions]) => {
                    const categoryNumber = category.replace('category_', '');
                    const categoryName = SCOPE3_CATEGORIES[categoryNumber] || category;
                    return (
                      <div key={category} className="bg-gray-900 rounded-lg p-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="text-sm font-medium text-gray-200">Category {categoryNumber}</p>
                            <p className="text-xs text-gray-400">{categoryName}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-gray-100">{(emissions as number).toFixed(3)} tCO₂e</p>
                            <p className="text-xs text-gray-500">
                              {(((emissions as number) / results.summary.scope3_emissions * 1000) * 100).toFixed(1)}% of Scope 3
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Detailed Breakdown */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-100 mb-4">Detailed Activity Breakdown</h3>
            <div className="space-y-2">
              {results.enhancedBreakdown
                .sort((a: any, b: any) => b.emissions_kg_co2e - a.emissions_kg_co2e)
                .map((item: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center">
                        {getIcon(item.iconType || 'Activity')}
                      </div>
                      <div>
                        <p className="text-sm text-gray-200">{item.name}</p>
                        <p className="text-xs text-gray-500">
                          {item.amount} {item.unit} × {item.factor || 'N/A'} kg CO₂e/{item.unit}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-100">{item.emissions_tons.toFixed(3)} tCO₂e</p>
                      {item.uncertainty_percentage && (
                        <p className="text-xs text-gray-500">
                          ±{item.uncertainty_percentage}%
                        </p>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Metadata */}
          <div className="bg-gray-900 rounded-lg p-4 text-xs text-gray-400">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span>Calculation Date: {new Date(results.metadata.calculation_date).toLocaleString()}</span>
              {results.metadata.monte_carlo_iterations > 0 && (
                <span>Monte Carlo Iterations: {results.metadata.monte_carlo_iterations.toLocaleString()}</span>
              )}
              <span>Reporting Period: {results.metadata.reporting_period}</span>
              <span>Activities: {results.metadata.total_activities}</span>
              {dataQualityScore && (
                <span>Data Quality: {dataQualityScore.overallScore.toFixed(0)}%</span>
              )}
              {results.metadata.has_esrs_e1_data && (
                <span className="text-green-400">ESRS E1 Data Included</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Export Dialog */}
      <ExportDialog />
    </div>
  );
};

export default EliteGHGCalculator;
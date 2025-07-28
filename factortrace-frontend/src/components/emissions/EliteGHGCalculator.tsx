import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart, RadialBarChart, RadialBar, Cell, PieChart, Pie } from 'recharts';
import { Activity, Zap, Cloud, Plane, Calculator, TrendingUp, AlertCircle, CheckCircle, Factory, Truck, Droplet, Flame, Snowflake, Package, Building2, Fuel, Trash2, Car, Home, Store, DollarSign, Recycle, ChevronDown, Wind, Download, Upload, FileText, Shield, Paperclip, Battery, Leaf, Euro, Users, Target, BarChart3 } from 'lucide-react';
import { generatePDFReport, generateBulkPDFReports, usePDFExport, PDFExportData } from './pdf-export-handler';

/**
 * EliteGHGCalculator Component
 * 
 * A comprehensive GHG emissions calculator with:
 * - Complete GHG Protocol coverage (Scope 1, 2, and all 15 Scope 3 categories)
 * - Monte Carlo uncertainty analysis
 * - Evidence upload and data quality scoring
 * - Multiple export formats (JSON, PDF, iXBRL)
 * - ESRS E1 compliant reporting
 * 
 * PDF Export Integration:
 * - Uses pdf-export-handler.ts for professional multi-page PDF generation
 * - Includes cover page, executive summary, charts, and certification
 * - Fallback to client-side generation if backend unavailable
 * - Requires: jspdf, jspdf-autotable, @types/jspdf, html2canvas
 */

interface EliteGHGCalculatorProps {
  companyId?: string;
  companyName?: string;
  reportingPeriod?: string;
  onCalculationComplete?: (data: any) => void;
}

// Add new interfaces for evidence and data quality
interface EvidenceFile {
  id: string;
  emission_id: number;
  fileName: string;
  fileType: string;
  uploadDate: Date;
  evidence_type: string;
  description?: string;
}

interface DataQualityMetrics {
  dataCompleteness: number;
  evidenceProvided: number;
  dataRecency: number;
  methodologyAccuracy: number;
  overallScore: number;
}

// ESRS E1 Interfaces
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

// Type definitions
interface EmissionOption {
  id: string;
  name: string;
  unit: string;
  factor: number;
  source: string;
}

interface EmissionCategory {
  name: string;
  icon: React.ReactNode;
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
  icon: React.ReactNode;
  evidence?: EvidenceFile[];
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
}

// ORGANIZED BY SCOPE - COMPLETE WITH ALL 15 SCOPE 3 CATEGORIES
const EMISSION_SCOPES: Record<string, EmissionScope> = {
  scope1: {
    name: "Scope 1 - Direct Emissions",
    description: "Direct GHG emissions from sources owned or controlled by the company",
    color: "red",
    categories: {
      stationary_combustion: {
        name: "Stationary Combustion",
        icon: <Factory className="w-5 h-5" />,
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
        icon: <Truck className="w-5 h-5" />,
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
        icon: <Cloud className="w-5 h-5" />,
        options: [
          { id: "industrial_process", name: "Industrial Process", unit: "tonnes", factor: 1000.0, source: "Custom" },
          { id: "chemical_production", name: "Chemical Production", unit: "tonnes", factor: 1500.0, source: "IPCC" }
        ]
      },
      fugitive_emissions: {
        name: "Fugitive Emissions",
        icon: <Wind className="w-5 h-5" />,
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
        icon: <Zap className="w-5 h-5" />,
        options: [
          { id: "electricity_grid", name: "Grid Electricity (Location-based)", unit: "kWh", factor: 0.233, source: "National Grid 2023" },
          { id: "electricity_renewable", name: "100% Renewable (Market-based)", unit: "kWh", factor: 0.0, source: "Supplier Specific" },
          { id: "electricity_partial_green", name: "Partial Renewable Mix", unit: "kWh", factor: 0.116, source: "Supplier Mix" }
        ]
      },
      purchased_heat: {
        name: "Purchased Heat/Steam/Cooling",
        icon: <Flame className="w-5 h-5" />,
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
        icon: <Package className="w-5 h-5" />,
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
        icon: <Building2 className="w-5 h-5" />,
        options: [
          { id: "machinery", name: "Machinery & Equipment", unit: "EUR", factor: 0.32, source: "EPA EEIO (EUR adjusted)" },
          { id: "buildings", name: "Buildings & Construction", unit: "EUR", factor: 0.26, source: "EPA EEIO (EUR adjusted)" },
          { id: "vehicles", name: "Vehicles", unit: "EUR", factor: 0.37, source: "EPA EEIO (EUR adjusted)" }
        ]
      },
      fuel_energy: {
        name: "3. Fuel & Energy Activities",
        icon: <Fuel className="w-5 h-5" />,
        options: [
          { id: "upstream_electricity", name: "Upstream Electricity", unit: "kWh", factor: 0.045, source: "DEFRA 2023" },
          { id: "upstream_natural_gas", name: "Upstream Natural Gas", unit: "kWh", factor: 0.035, source: "DEFRA 2023" },
          { id: "transmission_losses", name: "T&D Losses", unit: "kWh", factor: 0.020, source: "DEFRA 2023" }
        ]
      },
      upstream_transport: {
        name: "4. Upstream Transportation",
        icon: <Truck className="w-5 h-5" />,
        options: [
          { id: "road_freight", name: "Road Freight", unit: "tonne.km", factor: 0.096, source: "DEFRA 2023" },
          { id: "rail_freight", name: "Rail Freight", unit: "tonne.km", factor: 0.025, source: "DEFRA 2023" },
          { id: "sea_freight", name: "Sea Freight", unit: "tonne.km", factor: 0.016, source: "DEFRA 2023" },
          { id: "air_freight", name: "Air Freight", unit: "tonne.km", factor: 1.23, source: "DEFRA 2023" }
        ]
      },
      waste: {
        name: "5. Waste Generated",
        icon: <Trash2 className="w-5 h-5" />,
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
        icon: <Plane className="w-5 h-5" />,
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
        icon: <Car className="w-5 h-5" />,
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
        icon: <Building2 className="w-5 h-5" />,
        options: [
          { id: "leased_buildings", name: "Leased Buildings Energy", unit: "kWh", factor: 0.233, source: "Grid average" },
          { id: "leased_vehicles", name: "Leased Vehicle Fleet", unit: "km", factor: 0.171, source: "DEFRA 2023" },
          { id: "leased_equipment", name: "Leased Equipment", unit: "hours", factor: 5.5, source: "Estimated" },
          { id: "data_centers", name: "Leased Data Centers", unit: "kWh", factor: 0.233, source: "Grid average" }
        ]
      },
      downstream_transport: {
        name: "9. Downstream Transportation",
        icon: <Truck className="w-5 h-5" />,
        options: [
          { id: "product_delivery", name: "Product Delivery", unit: "tonne.km", factor: 0.096, source: "DEFRA 2023" },
          { id: "customer_collection", name: "Customer Collection", unit: "trips", factor: 2.5, source: "Estimated" },
          { id: "third_party_logistics", name: "3PL Distribution", unit: "tonne.km", factor: 0.096, source: "DEFRA 2023" }
        ]
      },
      processing_sold: {
        name: "10. Processing of Sold Products",
        icon: <Factory className="w-5 h-5" />,
        options: [
          { id: "intermediate_processing", name: "Intermediate Product Processing", unit: "tonnes", factor: 125.0, source: "Industry average" },
          { id: "customer_manufacturing", name: "Customer Manufacturing", unit: "units", factor: 2.5, source: "LCA estimate" },
          { id: "further_processing", name: "Further Processing", unit: "tonnes", factor: 85.0, source: "Estimated" }
        ]
      },
      use_of_products: {
        name: "11. Use of Sold Products",
        icon: <Zap className="w-5 h-5" />,
        options: [
          { id: "product_electricity", name: "Product Energy Use", unit: "kWh", factor: 0.233, source: "Grid average" },
          { id: "product_fuel", name: "Product Fuel Use", unit: "litres", factor: 2.31, source: "DEFRA 2023" },
          { id: "product_lifetime_energy", name: "Product Lifetime Energy", unit: "units", factor: 150.0, source: "LCA estimate" }
        ]
      },
      end_of_life: {
        name: "12. End-of-Life Treatment",
        icon: <Recycle className="w-5 h-5" />,
        options: [
          { id: "product_landfill", name: "Products to Landfill", unit: "tonnes", factor: 467.0, source: "DEFRA 2023" },
          { id: "product_recycling", name: "Products Recycled", unit: "tonnes", factor: 21.0, source: "DEFRA 2023" },
          { id: "product_incineration", name: "Products Incinerated", unit: "tonnes", factor: 21.0, source: "DEFRA 2023" }
        ]
      },
      downstream_leased: {
        name: "13. Downstream Leased Assets",
        icon: <Home className="w-5 h-5" />,
        options: [
          { id: "leased_real_estate", name: "Leased Real Estate", unit: "m2.year", factor: 55.0, source: "CRREM" },
          { id: "leased_equipment_downstream", name: "Leased Equipment (Customer)", unit: "units.year", factor: 150.0, source: "Estimated" },
          { id: "franchise_buildings", name: "Franchise Buildings", unit: "m2.year", factor: 55.0, source: "CRREM" }
        ]
      },
      franchises: {
        name: "14. Franchises",
        icon: <Store className="w-5 h-5" />,
        options: [
          { id: "franchise_energy", name: "Franchise Energy Use", unit: "kWh", factor: 0.233, source: "Grid average" },
          { id: "franchise_operations", name: "Franchise Operations", unit: "locations", factor: 25000.0, source: "Sector average" },
          { id: "franchise_travel", name: "Franchise Business Travel", unit: "EUR", factor: 0.14, source: "EPA EEIO (EUR adjusted)" },
          { id: "franchise_fleet", name: "Franchise Fleet", unit: "km", factor: 0.171, source: "DEFRA 2023" }
        ]
      },
      investments: {
        name: "15. Investments",
        icon: <DollarSign className="w-5 h-5" />,
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

// Helper function to show toast notifications
const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
  const toast = document.createElement('div');
  toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
    type === 'success' ? 'bg-green-600' : type === 'error' ? 'bg-red-600' : 'bg-blue-600'
  } text-white max-w-md`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  // Animate in
  toast.style.opacity = '0';
  toast.style.transform = 'translateY(1rem)';
  setTimeout(() => {
    toast.style.transition = 'all 0.3s ease-out';
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  }, 10);
  
  // Remove after delay
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(1rem)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
};

// Enhanced PDF Export Configuration
const PDF_EXPORT_CONFIG = {
  metadata: {
    title: 'GHG Emissions Report',
    subject: 'Corporate Greenhouse Gas Emissions Inventory',
    author: 'EliteGHGCalculator',
    keywords: 'GHG, emissions, carbon, ESRS E1, sustainability',
    creator: 'FactorTrace Platform'
  },
  sections: [
    'cover',
    'executive_summary',
    'emissions_overview',
    'scope_breakdown',
    'detailed_activities',
    'uncertainty_analysis',
    'data_quality',
    'evidence_documentation',
    'methodology',
    'certification'
  ],
  styling: {
    primaryColor: '#1a1a2e',
    secondaryColor: '#16213e',
    accentColor: '#0f3460',
    successColor: '#10b981',
    warningColor: '#f59e0b',
    dangerColor: '#ef4444'
  }
};

// Utility function to extract and analyze taxonomy tags from iXBRL export
const extractAllTaxonomyTags = async (exportData: any, apiUrl: string = 'http://localhost:8000') => {
  try {
    const response = await fetch(`${apiUrl}/api/v1/esrs-e1/export/esrs-e1-world-class`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(exportData)
    });
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Use result.xhtml_content instead of result.ixbrl
    const ixbrlContent = result.xhtml_content;
    
    // Extract all name attributes from taxonomy tags
    const namePattern = /name=["']([^"']+)["']/g;
    const taxonomyConcepts: string[] = [];
    let match;
    
    while ((match = namePattern.exec(ixbrlContent)) !== null) {
      taxonomyConcepts.push(match[1]);
    }
    
    console.log('All Taxonomy Concepts Used:');
    [...new Set(taxonomyConcepts)].sort().forEach(concept => {
      console.log(`  - ${concept}`);
    });
    
    // Count tag types
    const nonFractionCount = (ixbrlContent.match(/ix:nonFraction/g) || []).length;
    const nonNumericCount = (ixbrlContent.match(/ix:nonNumeric/g) || []).length;
    
    console.log(`\nTag Statistics:`);
    console.log(`  - ix:nonFraction tags: ${nonFractionCount}`);
    console.log(`  - ix:nonNumeric tags: ${nonNumericCount}`);
    console.log(`  - Total inline tags: ${nonFractionCount + nonNumericCount}`);
    
    return {
      taxonomyConcepts: [...new Set(taxonomyConcepts)].sort(),
      nonFractionCount,
      nonNumericCount,
      totalInlineTags: nonFractionCount + nonNumericCount,
      documentId: result.document_id
    };
  } catch (error) {
    console.error('Taxonomy extraction error:', error);
    throw error;
  }
};

// Evidence Upload Component
interface EvidenceUploadComponentProps {
  emissionId: number;
  onUploadSuccess?: (evidence: EvidenceFile) => void;
  existingEvidence?: EvidenceFile[];
}

const EvidenceUploadComponent: React.FC<EvidenceUploadComponentProps> = ({ 
  emissionId, 
  onUploadSuccess,
  existingEvidence = []
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<any>(null);
  const [evidenceType, setEvidenceType] = useState('invoice');
  const [showUploadForm, setShowUploadForm] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setUploadStatus({ error: 'File size exceeds 10MB limit' });
      return;
    }

    // Validate file type
    const allowedTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xlsx', '.xls', '.csv'];
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExt || '')) {
      setUploadStatus({ error: 'Invalid file type. Allowed: PDF, JPG, PNG, DOC, DOCX, XLSX, XLS, CSV' });
      return;
    }

    setUploading(true);
    setUploadStatus(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('emission_id', emissionId.toString());
      formData.append('evidence_type', evidenceType);
      formData.append('description', `Evidence for emission ${emissionId}`);

      const response = await fetch(`${API_URL}/api/v1/emissions/upload-evidence`, {
        method: 'POST',
        body: formData
        // Don't set Content-Type header - browser will set it with boundary for FormData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const result = await response.json();
      
      const newEvidence: EvidenceFile = {
        id: result.id || Date.now().toString(),
        emission_id: emissionId,
        fileName: file.name,
        fileType: file.type,
        uploadDate: new Date(),
        evidence_type: evidenceType,
        description: result.description
      };

      setUploadStatus({
        success: true,
        message: 'Evidence uploaded successfully!',
        data: result
      });

      // Notify parent component
      if (onUploadSuccess) {
        onUploadSuccess(newEvidence);
      }

      // Reset file input
      event.target.value = '';
      
      // Hide form after successful upload
      setTimeout(() => {
        setShowUploadForm(false);
        setUploadStatus(null);
      }, 2000);

    } catch (error: any) {
      setUploadStatus({
        error: error.message || 'Upload failed'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="evidence-upload-container">
      {!showUploadForm ? (
        <button
          onClick={() => setShowUploadForm(true)}
          className="flex items-center gap-1 text-sm text-gray-400 cursor-pointer hover:text-gray-300"
        >
          <Paperclip className="w-4 h-4" />
          <span>
            {existingEvidence.length > 0 ? (
              <span className="text-green-400">Evidence ({existingEvidence.length})</span>
            ) : (
              'Add Evidence'
            )}
          </span>
        </button>
      ) : (
        <div className="bg-gray-800 p-3 rounded-lg space-y-3">
          <div className="flex justify-between items-center">
            <h4 className="text-sm font-medium text-gray-200">Upload Evidence</h4>
            <button
              onClick={() => {
                setShowUploadForm(false);
                setUploadStatus(null);
              }}
              className="text-gray-400 hover:text-gray-300"
            >
              ×
            </button>
          </div>
          
          <div className="space-y-2">
            <div>
              <label htmlFor={`evidenceType-${emissionId}`} className="text-xs text-gray-400">
                Evidence Type:
              </label>
              <select 
                id={`evidenceType-${emissionId}`}
                value={evidenceType} 
                onChange={(e) => setEvidenceType(e.target.value)}
                disabled={uploading}
                className="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="invoice">Invoice</option>
                <option value="receipt">Receipt</option>
                <option value="meter_reading">Meter Reading</option>
                <option value="calculation_sheet">Calculation Sheet</option>
                <option value="photo">Photo</option>
                <option value="estimate">Estimate</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label htmlFor={`fileInput-${emissionId}`} className="text-xs text-gray-400">
                Select File:
              </label>
              <input
                id={`fileInput-${emissionId}`}
                type="file"
                onChange={handleFileSelect}
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xlsx,.xls,.csv"
                disabled={uploading}
                className="w-full text-xs text-gray-300 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:font-medium file:bg-gray-700 file:text-gray-200 hover:file:bg-gray-600"
              />
            </div>
          </div>

          {uploading && (
            <div className="flex items-center gap-2 text-sm text-blue-400">
              <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              <span>Uploading...</span>
            </div>
          )}

          {uploadStatus?.success && (
            <div className="bg-green-900/30 border border-green-600/30 rounded p-2">
              <p className="text-xs text-green-400">✅ {uploadStatus.message}</p>
              {uploadStatus.data?.quality_scores?.total_score && (
                <p className="text-xs text-green-400 mt-1">
                  Quality Score: {uploadStatus.data.quality_scores.total_score.toFixed(1)}%
                </p>
              )}
            </div>
          )}

          {uploadStatus?.error && (
            <div className="bg-red-900/30 border border-red-600/30 rounded p-2">
              <p className="text-xs text-red-400">❌ {uploadStatus.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ESRS E1 Data Collection Component
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
      
      {/* Tabs */}
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

      {/* Energy Consumption Tab */}
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
            
            {/* Calculated values */}
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

      {/* Carbon Pricing Tab */}
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

      {/* Climate Policy Tab */}
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

      {/* Climate Actions Tab */}
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

const EliteGHGCalculator: React.FC<EliteGHGCalculatorProps> = ({ 
  companyId = 'default',
  companyName = 'Your Company',
  reportingPeriod = new Date().toISOString().slice(0, 7),
  onCalculationComplete 
}) => {
  
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isCalculating, setIsCalculating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [monteCarloIterations, setMonteCarloIterations] = useState(10000);
  const [showUncertainty, setShowUncertainty] = useState(true);
  const [expandedScopes, setExpandedScopes] = useState<string[]>(['scope1']);
  const [expandedCategories, setExpandedCategories] = useState<string[]>([]);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [evidenceFiles, setEvidenceFiles] = useState<EvidenceFile[]>([]);
  const [dataQualityScore, setDataQualityScore] = useState<DataQualityMetrics | null>(null);
  const [showESRSE1, setShowESRSE1] = useState(false);
  const [esrsE1Data, setEsrsE1Data] = useState<ESRSE1Data>({});
  const [includeGasBreakdown, setIncludeGasBreakdown] = useState(true);
  const [showBulkExportDialog, setShowBulkExportDialog] = useState(false);
  const [bulkExportProgress, setBulkExportProgress] = useState(0);
  const [isBulkExporting, setIsBulkExporting] = useState(false);
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  // Calculate data quality score whenever activities or evidence changes
  useEffect(() => {
    const score = calculateDataQualityScore();
    setDataQualityScore(score);
  }, [activities, evidenceFiles]);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      setBackendStatus(response.ok ? 'online' : 'offline');
    } catch {
      setBackendStatus('offline');
    }
  };

  // FIXED: Prepare comprehensive PDF export data with correct unit conversions
  // FIXED: Prepare comprehensive PDF export data
  const preparePDFExportData = () => {
    if (!results) return null;
    
    console.log('DEBUG - API Results:', results); // Debug log
    
    // Helper function to safely parse numbers
    const safeParseNumber = (value: any): number => {
      if (typeof value === 'number') return value;
      if (typeof value === 'string') return parseFloat(value) || 0;
      return 0;
    };
    
    // Helper function to calculate scope totals from activities
    const calculateScopeFromActivities = (scopeId: string): number => {
      return activities
        .filter(a => a.scopeId === scopeId)
        .reduce((sum, activity) => {
          const amount = safeParseNumber(activity.amount);
          const factor = safeParseNumber(activity.factor);
          return sum + (amount * factor) / 1000; // Convert kg to tons
        }, 0);
    };
    
    // Extract values from API response - handle all possible field names
    const apiSummary = results.summary || {};
    
    // Total emissions - check multiple possible field names
    const totalFromAPI = apiSummary.totalEmissions || 
                        apiSummary.total_emissions_tons_co2e || 
                        apiSummary.total_emissions ||
                        apiSummary.totalCO2e || 0;
    
    // Scope 1 - check all variations
    const scope1FromAPI = apiSummary.scope1 || 
                         apiSummary.scope1_emissions || 
                         apiSummary.scope1_total ||
                         apiSummary.scope1Emissions || 0;
    
    // Scope 2 - check all variations INCLUDING location/market based
    const scope2LocationFromAPI = apiSummary.scope2 || 
                                 apiSummary.scope2_emissions ||
                                 apiSummary.scope2_location_based || 
                                 apiSummary.scope2_location ||
                                 apiSummary.scope2LocationBased ||
                                 apiSummary.scope2_total || 0;
    
    const scope2MarketFromAPI = apiSummary.scope2_market_based || 
                               apiSummary.scope2_market ||
                               apiSummary.scope2Market ||
                               apiSummary.scope2MarketBased || 
                               scope2LocationFromAPI; // Default to location-based
    
    // Scope 3 - check all variations
    const scope3FromAPI = apiSummary.scope3 || 
                         apiSummary.scope3_emissions || 
                         apiSummary.scope3_total ||
                         apiSummary.scope3Emissions || 0;
    
    // Determine if values are in kg or tons
    // If total is much smaller than sum of scopes, scopes are likely in kg
    const sumOfScopes = scope1FromAPI + scope2LocationFromAPI + scope3FromAPI;
    const needsConversion = totalFromAPI > 0 && sumOfScopes > totalFromAPI * 100;
    
    // Convert to tons with intelligent detection
    let scope1InTons, scope2InTons, scope2MarketInTons, scope3InTons;
    
    if (needsConversion || sumOfScopes > 100) {
      // Values are likely in kg, convert to tons
      scope1InTons = scope1FromAPI / 1000;
      scope2InTons = scope2LocationFromAPI / 1000;
      scope2MarketInTons = scope2MarketFromAPI / 1000;
      scope3InTons = scope3FromAPI / 1000;
    } else {
      // Values might already be in tons, but verify
      scope1InTons = scope1FromAPI;
      scope2InTons = scope2LocationFromAPI;
      scope2MarketInTons = scope2MarketFromAPI;
      scope3InTons = scope3FromAPI;
    }
    
    // Calculate from activities as backup
    const scope1Calculated = calculateScopeFromActivities('scope1');
    const scope2Calculated = calculateScopeFromActivities('scope2');
    const scope3Calculated = calculateScopeFromActivities('scope3');
    
    // Use calculated values if API values seem wrong (e.g., scope2 is 0 but we have activities)
    if (scope2InTons === 0 && scope2Calculated > 0) {
      console.warn('Using calculated Scope 2 value as API returned 0');
      scope2InTons = scope2Calculated;
    }
    
    // Reconcile totals
    const calculatedTotal = scope1InTons + scope2InTons + scope3InTons;
    const totalEmissions = calculatedTotal; // Use calculated total for consistency
    
    // Calculate percentages
    const scope1Percentage = totalEmissions > 0 ? (scope1InTons / totalEmissions) * 100 : 0;
    const scope2Percentage = totalEmissions > 0 ? (scope2InTons / totalEmissions) * 100 : 0;
    const scope3Percentage = totalEmissions > 0 ? (scope3InTons / totalEmissions) * 100 : 0;
    
    console.log('DEBUG - Calculated values:', {
      scope1InTons,
      scope2InTons,
      scope3InTons,
      totalEmissions,
      percentages: { scope1: scope1Percentage, scope2: scope2Percentage, scope3: scope3Percentage }
    });
    
    // Process breakdown/activities
    const breakdown = results.enhancedBreakdown || results.breakdown || [];
    
    // Identify top emission sources from activities
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
    
    // Prepare scope 3 category analysis
    const scope3Categories = {};
    
    // Process activities to build scope 3 analysis
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
        scope3Categories[categoryName].hasEvidence = 
          scope3Categories[categoryName].hasEvidence || 
          (activity.evidence && activity.evidence.length > 0);
      });
    
    const scope3Analysis = Object.values(scope3Categories).map((cat: any) => ({
      ...cat,
      percentage: scope3InTons > 0 ? (cat.emissions / scope3InTons) * 100 : 0
    }));
    
    // Build final PDF data structure
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
        evidenceCount: evidenceFiles?.length || 0
      },
      topEmissionSources,
      scope3Analysis,
      activities: activities.map(a => ({
        ...a,
        emissions: (safeParseNumber(a.amount) * safeParseNumber(a.factor)) / 1000
      })),
      evidenceFiles: evidenceFiles || [],
      uncertaintyAnalysis: results.uncertainty_analysis || null,
      dataQuality: dataQualityScore || null,
      chartElements: [], // Add if you have charts to include
      companyProfile: {
        sector: 'Services', // Update based on your data
        employees: 0,
        revenue: 0,
        operations: []
      }
    };
    
    return pdfData;
  };

  // Calculate Data Quality Score
  const calculateDataQualityScore = (): DataQualityMetrics => {
    if (!activities || activities.length === 0) {
      return {
        dataCompleteness: 0,
        evidenceProvided: 0,
        dataRecency: 0,
        methodologyAccuracy: 0,
        overallScore: 0
      };
    }
    
    // Data Completeness (25%)
    const totalFields = activities.length * 2; // amount and unit are required
    const filledFields = activities.filter(a => 
      a.amount && parseFloat(String(a.amount)) > 0 && a.unit
    ).length * 2;
    const dataCompleteness = totalFields > 0 ? (filledFields / totalFields) * 100 : 0;
    
    // Evidence Provided (25%)
    const activitiesWithEvidence = new Set(evidenceFiles.map(e => e.emission_id)).size;
    const evidenceProvided = activities.length > 0 ? (activitiesWithEvidence / activities.length) * 100 : 0;
    
    // Data Recency (25%) - Based on reporting period
    const currentDate = new Date();
    const reportingDate = new Date(reportingPeriod);
    const monthsDiff = (currentDate.getFullYear() - reportingDate.getFullYear()) * 12 + 
                      (currentDate.getMonth() - reportingDate.getMonth());
    const dataRecency = Math.max(0, 100 - (monthsDiff * 5)); // Lose 5% per month old
    
    // Methodology Accuracy (25%) - Based on emission factor sources
    const accurateMethodologies = activities.filter(a => 
      a.source && (a.source.includes('DEFRA') || a.source.includes('EPA') || a.source.includes('IPCC'))
    ).length;
    const methodologyAccuracy = activities.length > 0 ? (accurateMethodologies / activities.length) * 100 : 0;
    
    // Overall Score
    const overallScore = (
      dataCompleteness * 0.25 +
      evidenceProvided * 0.25 +
      dataRecency * 0.25 +
      methodologyAccuracy * 0.25
    );
    
    return {
      dataCompleteness,
      evidenceProvided,
      dataRecency,
      methodologyAccuracy,
      overallScore
    };
  };

  // Handle evidence upload
  const handleEvidenceUpload = async (activityId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('emission_id', activityId.toString());
    formData.append('evidence_type', 'invoice'); // You can make this dynamic
    formData.append('description', `Evidence for ${activities.find(a => a.id === activityId)?.name || 'activity'}`);
    
    try {
      const response = await fetch(`${API_URL}/api/v1/emissions/upload-evidence`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        const newEvidence: EvidenceFile = {
          id: result.id || Date.now().toString(),
          emission_id: activityId,
          fileName: file.name,
          fileType: file.type,
          uploadDate: new Date(),
          evidence_type: 'invoice',
          description: result.description
        };
        
        setEvidenceFiles([...evidenceFiles, newEvidence]);
        
        // Update activity to show it has evidence
        setActivities(prev => prev.map(a => 
          a.id === activityId 
            ? { ...a, evidence: [...(a.evidence || []), newEvidence] }
            : a
        ));
        
        showToast('Evidence uploaded successfully', 'success');
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Evidence upload failed:', error);
      showToast('Failed to upload evidence', 'error');
    }
  };

  // Enhanced export function with format selection
  const handleExportResults = () => {
    if (!results) {
      showToast('No results to export', 'error');
      return;
    }
    setShowExportDialog(true);
  };

  const handleExportFormat = async (format: 'json' | 'pdf' | 'ixbrl' | 'ixbrl-debug') => {
    setShowExportDialog(false);
    
    try {
      if (format === 'json') {
        exportAsJSON();
      } else if (format === 'pdf') {
        await exportAsPDF();
      } else if (format === 'ixbrl') {
        await exportAsIXBRL();
      } else if (format === 'ixbrl-debug') {
        await exportAsIXBRLWithDebug();
      }
    } catch (error) {
      console.error(`Export failed for ${format}:`, error);
      showToast(`Failed to export as ${format.toUpperCase()}`, 'error');
    }
  };

  const exportAsJSON = () => {
    const exportData = {
      metadata: {
        ...results.metadata,
        dataQuality: dataQualityScore
      },
      summary: results.summary,
      uncertainty_analysis: results.uncertainty_analysis,
      breakdown: results.enhancedBreakdown,
      categoryTotals: results.categoryTotals,
      activities: activities,
      evidenceFiles: evidenceFiles,
      esrs_e1_data: esrsE1Data,
      ghg_breakdown: results.ghg_breakdown,
      generated_at: new Date().toISOString()
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

  // ENHANCED: Export as PDF function with bulk support
  const exportAsPDF = async (options?: { bulk?: boolean; documents?: PDFExportData[] }) => {
    if (options?.bulk && options.documents) {
      // Bulk export mode
      setShowBulkExportDialog(true);
      setIsBulkExporting(true);
      setBulkExportProgress(0);

      try {
        const results = await generateBulkPDFReports(options.documents, {
          parallelLimit: 3,
          retryAttempts: 2,
          compressionLevel: 'fast',
          onProgress: (progress, currentDoc) => {
            setBulkExportProgress(progress);
            showToast(`Exporting: ${currentDoc} (${progress.toFixed(0)}%)`, 'info');
          },
          onComplete: (results) => {
            const successful = results.filter(r => r.success).length;
            const failed = results.filter(r => !r.success).length;
            
            showToast(
              `✅ Bulk export complete! ${successful} successful, ${failed} failed`,
              failed > 0 ? 'error' : 'success'
            );
          },
          apiUrl: API_URL
        });

        return results;
      } finally {
        setIsBulkExporting(false);
        setTimeout(() => setShowBulkExportDialog(false), 2000);
      }
    } else {
      // Single export mode
      showToast('Generating PDF report...', 'info');
      
      try {
        const pdfData = preparePDFExportData();
        
        if (!pdfData) {
          showToast('No data available for PDF export', 'error');
          return;
        }

        console.log('Starting PDF export with data:', pdfData);

        // Use the high-performance handler with automatic fallback
        const result = await generatePDFReport(pdfData, {
          useBackend: true, // Will automatically fallback to client-side if backend fails
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
    }
  };

  // New enhanced iXBRL export function
  const exportAsIXBRL = async () => {
    showToast('Generating iXBRL file...', 'info');
    
    try {
      // Map the scope 3 categories from results to the expected format
      const scope3Categories = [
        'purchased_goods', 'capital_goods', 'fuel_energy', 'upstream_transport',
        'waste', 'business_travel', 'employee_commuting', 'upstream_leased',
        'downstream_transport', 'processing_sold', 'use_of_products', 'end_of_life',
        'downstream_leased', 'franchises', 'investments'
      ];
      
      const scope3_detailed: any = {};
      
      // Calculate emissions for each Scope 3 category
      scope3Categories.forEach((categoryId, index) => {
        const categoryNum = index + 1;
        let categoryEmissions = 0;
        
        // Find all activities for this category
        if (results && results.enhancedBreakdown) {
          const categoryActivities = results.enhancedBreakdown.filter((item: any) => 
            item.scopeId === 'scope3' && item.categoryId === categoryId
          );
          
          categoryEmissions = categoryActivities.reduce((sum: number, activity: any) => 
            sum + (activity.emissions_tons || 0), 0
          );
        }
        
        scope3_detailed[`category_${categoryNum}`] = {
          emissions_tco2e: categoryEmissions,
          excluded: categoryEmissions === 0
        };
      });
      
      const exportData = {
        organization: companyName,
        reporting_period: new Date(reportingPeriod).getFullYear(),
        force_generation: true, // Remove when you have complete data
        scope3_detailed: scope3_detailed,
        // Add other required fields based on your results
        total_emissions: results?.summary?.total_emissions_tons_co2e || 0,
        scope1: results?.summary?.scope1_emissions ? results.summary.scope1_emissions / 1000 : 0,
        scope2_location: results?.summary?.scope2_location_based ? results.summary.scope2_location_based / 1000 : 0,
        scope2_market: results?.summary?.scope2_market_based ? results.summary.scope2_market_based / 1000 : 0,
        scope3_total: results?.summary?.scope3_emissions ? results.summary.scope3_emissions / 1000 : 0,
        // Add ESRS E1 data
        esrs_e1_data: esrsE1Data,
        ghg_breakdown: results?.ghg_breakdown
      };
      
      const response = await fetch(`${API_URL}/api/v1/esrs-e1/export/esrs-e1-world-class`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportData)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('iXBRL export error:', errorText);
        throw new Error('Export failed');
      }
      
      const result = await response.json();
      
      // Create a download link for the iXBRL file
      const blob = new Blob([result.xhtml_content], { type: 'application/xhtml+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ESRS_E1_Report_${result.document_id}.xhtml`;
      a.click();
      URL.revokeObjectURL(url);
      
      // Show success message
      showToast(`✅ Export successful! Document ID: ${result.document_id}`, 'success');
      
    } catch (error: any) {
      console.error('Export error:', error);
      showToast(`❌ Export failed: ${error.message}`, 'error');
    }
  };

  // iXBRL export with debug information
  const exportAsIXBRLWithDebug = async () => {
    showToast('Generating iXBRL with taxonomy analysis...', 'info');
    
    try {
      // Prepare the same export data as regular iXBRL export
      const scope3Categories = [
        'purchased_goods', 'capital_goods', 'fuel_energy', 'upstream_transport',
        'waste', 'business_travel', 'employee_commuting', 'upstream_leased',
        'downstream_transport', 'processing_sold', 'use_of_products', 'end_of_life',
        'downstream_leased', 'franchises', 'investments'
      ];
      
      const scope3_detailed: any = {};
      
      scope3Categories.forEach((categoryId, index) => {
        const categoryNum = index + 1;
        let categoryEmissions = 0;
        
        if (results && results.enhancedBreakdown) {
          const categoryActivities = results.enhancedBreakdown.filter((item: any) => 
            item.scopeId === 'scope3' && item.categoryId === categoryId
          );
          
          categoryEmissions = categoryActivities.reduce((sum: number, activity: any) => 
            sum + (activity.emissions_tons || 0), 0
          );
        }
        
        scope3_detailed[`category_${categoryNum}`] = {
          emissions_tco2e: categoryEmissions,
          excluded: categoryEmissions === 0
        };
      });
      
      const exportData = {
        organization: companyName,
        reporting_period: new Date(reportingPeriod).getFullYear(),
        force_generation: true,
        scope3_detailed: scope3_detailed,
        total_emissions: results?.summary?.total_emissions_tons_co2e || 0,
        scope1: results?.summary?.scope1_emissions ? results.summary.scope1_emissions / 1000 : 0,
        scope2_location: results?.summary?.scope2_location_based ? results.summary.scope2_location_based / 1000 : 0,
        scope2_market: results?.summary?.scope2_market_based ? results.summary.scope2_market_based / 1000 : 0,
        scope3_total: results?.summary?.scope3_emissions ? results.summary.scope3_emissions / 1000 : 0,
        esrs_e1_data: esrsE1Data,
        ghg_breakdown: results?.ghg_breakdown
      };
      
      // First, extract taxonomy information
      const taxonomyInfo = await extractAllTaxonomyTags(exportData, API_URL);
      
      // Then proceed with regular export
      const response = await fetch(`${API_URL}/api/v1/esrs-e1/export/esrs-e1-world-class`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportData)
      });
      
      if (!response.ok) {
        throw new Error('Export failed');
      }
      
      const result = await response.json();
      
      // Create downloads for both the iXBRL file and taxonomy analysis
      const blob = new Blob([result.xhtml_content], { type: 'application/xhtml+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ESRS_E1_Report_${result.document_id}.xhtml`;
      a.click();
      URL.revokeObjectURL(url);
      
      // Create a debug report
      const debugReport = `ESRS E1 iXBRL Export Debug Report
Document ID: ${result.document_id}
Generated: ${new Date().toISOString()}

TAXONOMY CONCEPTS USED:
${taxonomyInfo.taxonomyConcepts.map(c => `  - ${c}`).join('\n')}

TAG STATISTICS:
  - ix:nonFraction tags: ${taxonomyInfo.nonFractionCount}
  - ix:nonNumeric tags: ${taxonomyInfo.nonNumericCount}
  - Total inline tags: ${taxonomyInfo.totalInlineTags}

EMISSIONS SUMMARY:
  - Total: ${exportData.total_emissions} tCO2e
  - Scope 1: ${exportData.scope1} tCO2e
  - Scope 2 (Location): ${exportData.scope2_location} tCO2e
  - Scope 2 (Market): ${exportData.scope2_market} tCO2e
  - Scope 3: ${exportData.scope3_total} tCO2e

GHG BREAKDOWN:
${results?.ghg_breakdown ? `
  - CO2: ${results.ghg_breakdown.CO2_tonnes.toFixed(2)} tonnes
  - CH4: ${results.ghg_breakdown.CH4_tonnes.toFixed(2)} tonnes
  - N2O: ${results.ghg_breakdown.N2O_tonnes.toFixed(2)} tonnes
  - Total CO2e: ${results.ghg_breakdown.total_co2e.toFixed(2)} tonnes
  - GWP Version: ${results.ghg_breakdown.gwp_version}
` : '  - Not calculated'}

ESRS E1 DATA:
${esrsE1Data ? `
  - Energy Consumption: ${esrsE1Data.energy_consumption ? 'Provided' : 'Missing'}
  - Internal Carbon Pricing: ${esrsE1Data.internal_carbon_pricing?.implemented ? 'Implemented' : 'Not implemented'}
  - Climate Policy: ${esrsE1Data.climate_policy?.has_climate_policy ? 'Established' : 'Missing'}
  - Climate Actions: ${esrsE1Data.climate_actions ? 'Documented' : 'Missing'}
` : '  - No ESRS E1 data provided'}

SCOPE 3 BREAKDOWN:
${Object.entries(scope3_detailed).map(([cat, data]: [string, any]) => 
  `  - ${cat}: ${data.emissions_tco2e} tCO2e ${data.excluded ? '(excluded)' : ''}`
).join('\n')}
`;
      
      // Download debug report
      const debugBlob = new Blob([debugReport], { type: 'text/plain' });
      const debugUrl = URL.createObjectURL(debugBlob);
      const debugLink = document.createElement('a');
      debugLink.href = debugUrl;
      debugLink.download = `ESRS_E1_Debug_${result.document_id}.txt`;
      debugLink.click();
      URL.revokeObjectURL(debugUrl);
      
      showToast(`✅ Export successful with debug info! Document ID: ${result.document_id}`, 'success');
      
    } catch (error: any) {
      console.error('Export error:', error);
      showToast(`❌ Export failed: ${error.message}`, 'error');
    }
  };

  // Toggle scope expansion
  const toggleScope = (scopeId: string) => {
    setExpandedScopes(prev => 
      prev.includes(scopeId) 
        ? prev.filter(s => s !== scopeId)
        : [...prev, scopeId]
    );
  };

  // Toggle category expansion
  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => 
      prev.includes(categoryId) 
        ? prev.filter(c => c !== categoryId)
        : [...prev, categoryId]
    );
  };

  // Add activity
  const addActivity = (scopeId: string, categoryId: string, optionId: string) => {
    const scope = EMISSION_SCOPES[scopeId];
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
        icon: category.icon,
        evidence: []
      };
      setActivities([...activities, newActivity]);
      showToast(`Added: ${option.name}`, 'success');
    }
  };

  // Update activity
  const updateActivity = (id: number, field: string, value: any) => {
    setActivities(prev => prev.map(a => 
      a.id === id ? { ...a, [field]: value } : a
    ));
  };

  // Remove activity
  const removeActivity = (id: number) => {
    setActivities(prev => prev.filter(a => a.id !== id));
    // Also remove associated evidence
    setEvidenceFiles(prev => prev.filter(e => e.emission_id !== id));
    showToast('Activity removed', 'info');
  };

  // Calculate emissions with proper error handling
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
      // Prepare data for API
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
          reporting_period: reportingPeriod,
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
      
      // Process and enhance results
      const processedResults = processResults(data, activeActivities);
      setResults(processedResults);
      
      // Notify parent component
      if (onCalculationComplete) {
        onCalculationComplete(processedResults);
      }
      
      // Success message with proper null checking
      const totalEmissions = data.summary.total_emissions_tons_co2e;
      let message = `✅ Total: ${totalEmissions.toFixed(2)} tCO₂e`;
      
      if (data.uncertainty_analysis && showUncertainty && data.uncertainty_analysis.confidence_interval_95) {
        const [lower, upper] = data.uncertainty_analysis.confidence_interval_95;
        message += ` (${(lower / 1000).toFixed(2)} - ${(upper / 1000).toFixed(2)} tCO₂e with 95% confidence)`;
      }
      
      showToast(message, 'success');
      
    } catch (error: any) {
      console.error('Calculation failed:', error);
      
      // Detailed error messages
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

  // Process results with proper data mapping
  const processResults = (apiData: APIResponse, activeActivities: Activity[]) => {
    const summary = apiData.summary;
    
    // Map backend activity types to frontend
    const backendToFrontend: Record<string, string> = {
      'electricity': 'electricity_grid',
      'natural gas': 'natural_gas_stationary',
      'diesel': 'diesel_fleet',
      'gasoline': 'petrol_fleet',
      // Add more mappings as needed
    };
    
    // Create activity map for quick lookup
    const activityMap = new Map<string, Activity>();
    activeActivities.forEach(a => {
      activityMap.set(a.optionId, a);
    });
    
    // Enhanced breakdown with frontend data
    const enhancedBreakdown = apiData.breakdown.map((item) => {
      // Try to find the activity by direct match or through mapping
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
        icon: activity?.icon || <Activity className="w-5 h-5" />
      };
    });
    
    // Group by category with proper structure
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
          icon: item.icon
        };
      }
      
      acc[key].emissions += item.emissions_tons;
      acc[key].emissions_kg_co2e += item.emissions_kg_co2e;
      acc[key].items.push(item);
      
      return acc;
    }, {});
    
    // Calculate metadata
    const metadata = {
      calculation_date: apiData.calculation_date,
      reporting_period: apiData.reporting_period,
      monte_carlo_iterations: apiData.uncertainty_analysis?.monte_carlo_runs || 0,
      total_activities: activeActivities.length,
      data_quality_score: dataQualityScore,
      has_esrs_e1_data: !!esrsE1Data && Object.keys(esrsE1Data).length > 0
    };
    
    return {
      ...apiData,
      enhancedBreakdown,
      categoryTotals: Object.values(categoryTotals).sort((a: any, b: any) => b.emissions - a.emissions),
      chartData: prepareChartData(summary, categoryTotals),
      metadata,
      ghg_breakdown: apiData.ghg_breakdown,
      esrs_e1_metadata: apiData.esrs_e1_metadata
    };
  };

  // Prepare data for charts with proper null checking
  const prepareChartData = (summary: any, categoryTotals: any) => {
    // Scope breakdown for pie chart
    const scopeData = [
      { name: 'Scope 1', value: summary.scope1_emissions / 1000, fill: '#ef4444' },
      { name: 'Scope 2', value: summary.scope2_location_based / 1000, fill: '#3b82f6' },
      { name: 'Scope 3', value: summary.scope3_emissions / 1000, fill: '#10b981' }
    ].filter(item => item.value > 0);
    
    // Top categories for bar chart with proper null checking
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

  // Data Quality Indicator Component
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
              <span className="text-gray-400">Evidence Provided</span>
              <span className={getScoreColor(dataQualityScore.evidenceProvided)}>
                {dataQualityScore.evidenceProvided.toFixed(0)}%
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

  // Export Dialog Component
  const ExportDialog = () => {
    if (!showExportDialog) return null;
    
    // Check if debug mode is enabled (can be toggled with Ctrl+Shift+D)
    const [showDebugOption, setShowDebugOption] = useState(false);
    
    useEffect(() => {
      const handleKeyPress = (e: KeyboardEvent) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'D') {
          setShowDebugOption(prev => !prev);
        }
      };
      
      if (showExportDialog) {
        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
      }
    }, [showExportDialog]);
    
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
            {showDebugOption && (
              <button
                onClick={() => handleExportFormat('ixbrl-debug')}
                className="w-full px-4 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg flex items-center justify-between transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5" />
                  <span className="font-medium">iXBRL with Debug</span>
                </div>
                <span className="text-sm text-orange-200">Dev analysis</span>
              </button>
            )}
          </div>
          {!showDebugOption && (
            <p className="text-xs text-gray-500 mt-3 text-center">
              Press Ctrl+Shift+D for developer options
            </p>
          )}
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

  // Bulk Export Progress Dialog
  const BulkExportProgressDialog = () => {
    if (!showBulkExportDialog) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
          <h3 className="text-xl font-bold mb-4 text-white">Bulk PDF Export</h3>
          
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span>Progress</span>
              <span>{bulkExportProgress.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${bulkExportProgress}%` }}
              />
            </div>
          </div>
          
          {isBulkExporting && (
            <div className="flex items-center gap-2 text-sm text-blue-400">
              <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              <span>Generating PDF reports...</span>
            </div>
          )}
          
          {!isBulkExporting && bulkExportProgress === 100 && (
            <div className="text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
              <p className="text-green-400">Bulk export complete!</p>
            </div>
          )}
        </div>
      </div>
    );
  };

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
              {activities.length} activities added • {activities.filter(a => parseFloat(String(a.amount)) > 0).length} with values • {evidenceFiles.length} evidence files
            </span>
          </div>
          <button
            onClick={() => {
              setActivities([]);
              setEvidenceFiles([]);
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
        {Object.entries(EMISSION_SCOPES).map(([scopeId, scope]) => (
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
                          {category.icon}
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
            
            const scope = EMISSION_SCOPES[scopeId];
            
            return (
              <div key={scopeId} className="mb-6">
                <h4 className="text-sm font-medium text-gray-400 mb-3">{scope.name}</h4>
                <div className="space-y-2">
                  {scopeActivities.map(activity => (
                    <div key={activity.id} className="flex items-center gap-3 p-3 bg-gray-900 rounded-lg">
                      <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
                        {activity.icon}
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
                      {/* Evidence Upload Component */}
                      <EvidenceUploadComponent
                        emissionId={activity.id}
                        existingEvidence={activity.evidence}
                        onUploadSuccess={(newEvidence) => {
                          // Update evidence files state
                          setEvidenceFiles(prev => [...prev, newEvidence]);
                          
                          // Update activity to show it has evidence
                          setActivities(prev => prev.map(a => 
                            a.id === activity.id 
                              ? { ...a, evidence: [...(a.evidence || []), newEvidence] }
                              : a
                          ));
                          
                          showToast('Evidence uploaded successfully', 'success');
                        }}
                      />
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
                          {category.icon || <Activity className="w-5 h-5" />}
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

          {/* Evidence Summary */}
          {evidenceFiles.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-100 mb-4">
                Evidence Files ({evidenceFiles.length})
              </h3>
              <div className="space-y-2">
                {evidenceFiles.map((file, idx) => {
                  const activity = activities.find(a => a.id === file.emission_id);
                  return (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-sm text-gray-200">{file.fileName}</p>
                          <p className="text-xs text-gray-500">
                            {activity?.name || 'Unknown activity'} • {file.evidence_type}
                          </p>
                        </div>
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(file.uploadDate).toLocaleDateString()}
                      </span>
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
                        {item.icon || <Activity className="w-5 h-5" />}
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
      
      {/* Bulk Export Progress Dialog */}
      <BulkExportProgressDialog />
    </div>
  );
};

/**
 * Export Components
 * =================
 * 
 * EmissionDetail: Standalone component for displaying individual emission details
 * Can be used in emission lists or detail views throughout your application
 * 
 * PDF Export Handler Integration:
 * The component now fully supports the enhanced PDF export handler which provides:
 * - Professional multi-page PDF reports
 * - Automatic fallback between backend and client-side generation
 * - Executive-ready formatting and design
 * - Complete data coverage matching iXBRL exports
 * 
 * File Structure:
 * - EliteGHGCalculator.tsx (this file)
 * - pdf-export-handler.ts (PDF generation logic)
 * 
 * Both files should be in the same directory for proper integration.
 */

// Emission Detail Component (for integration with existing emissions list)
interface EmissionDetailProps {
  emission: {
    id: number;
    category: string;
    amount: number;
    unit: string;
    emissions_tco2e?: number;
  };
}

export const EmissionDetail: React.FC<EmissionDetailProps> = ({ emission }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-medium text-gray-100 mb-4">
        Emission: {emission.category}
      </h2>
      <p className="text-gray-300 mb-4">
        Amount: {emission.amount} {emission.unit}
        {emission.emissions_tco2e && (
          <span className="ml-2">
            ({emission.emissions_tco2e.toFixed(3)} tCO₂e)
          </span>
        )}
      </p>
      
      {/* Add the upload component */}
      <EvidenceUploadComponent 
        emissionId={emission.id}
        onUploadSuccess={(evidence) => {
          showToast(`Evidence uploaded for ${emission.category}`, 'success');
        }}
      />
    </div>
  );
};

export default EliteGHGCalculator;
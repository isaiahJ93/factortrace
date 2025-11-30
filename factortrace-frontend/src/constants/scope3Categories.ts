// src/constants/scope3Categories.ts

// Direct copy of SCOPE3_CATEGORIES constant
export const SCOPE3_CATEGORIES = {
  purchased_goods_services: {
    id: "cat1",
    displayName: "Purchased Goods and Services",
    ghgProtocolId: "3.1",
    description: "Extraction, production, and transportation of goods and services purchased or acquired by the reporting company in the reporting year",
    materialSectors: ["Manufacturing", "Retail", "Technology", "Healthcare"],
    esrsRequirements: ["E1-6.50", "E1-6.51"],
    cdpQuestions: ["C6.5", "C6.5a"],
    calculationGuidance: "Use supplier-specific method when available, otherwise activity-based, fallback to spend-based",
    examples: ["Raw materials", "Components", "Office supplies", "Professional services", "Software licenses", "Consulting services"]
  },
  capital_goods: {
    id: "cat2",
    displayName: "Capital Goods",
    ghgProtocolId: "3.2",
    description: "Extraction, production, and transportation of capital goods purchased or acquired by the reporting company in the reporting year",
    materialSectors: ["Manufacturing", "Real Estate", "Technology", "Energy"],
    esrsRequirements: ["E1-6.52"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Depreciate emissions over asset lifetime",
    examples: ["Buildings", "Machinery", "Equipment", "Vehicles", "IT infrastructure", "Furniture"]
  },
  fuel_energy_activities: {
    id: "cat3",
    displayName: "Fuel- and Energy-Related Activities",
    ghgProtocolId: "3.3",
    description: "Extraction, production, and transportation of fuels and energy purchased or acquired by the reporting company in the reporting year, not already accounted for in scope 1 or scope 2",
    materialSectors: ["All sectors"],
    esrsRequirements: ["E1-6.53"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Include WTT emissions and T&D losses",
    examples: ["Upstream emissions of purchased fuels", "T&D losses", "Generation of purchased electricity consumed"]
  },
  upstream_transportation: {
    id: "cat4",
    displayName: "Upstream Transportation and Distribution",
    ghgProtocolId: "3.4",
    description: "Transportation and distribution of products purchased by the reporting company in the reporting year between a company's tier 1 suppliers and its own operations",
    materialSectors: ["Retail", "Manufacturing", "E-commerce"],
    esrsRequirements: ["E1-6.54"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Use GLEC Framework for transport emissions",
    examples: ["Inbound logistics", "Warehousing purchased products", "Transportation between suppliers' facilities"]
  },
  waste_operations: {
    id: "cat5",
    displayName: "Waste Generated in Operations",
    ghgProtocolId: "3.5",
    description: "Disposal and treatment of waste generated in the reporting company's operations in the reporting year",
    materialSectors: ["Manufacturing", "Retail", "Healthcare", "Hospitality"],
    esrsRequirements: ["E1-6.55"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Apply waste-type-specific emission factors",
    examples: ["Disposal of solid waste", "Wastewater treatment", "Recycling", "Composting", "Incineration"]
  },
  business_travel: {
    id: "cat6",
    displayName: "Business Travel",
    ghgProtocolId: "3.6",
    description: "Transportation of employees for business-related activities during the reporting year",
    materialSectors: ["Professional Services", "Technology", "Finance"],
    esrsRequirements: ["E1-6.56"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Include all modes and accommodation",
    examples: ["Air travel", "Rail travel", "Ground transportation", "Hotel stays", "Rental cars"]
  },
  employee_commuting: {
    id: "cat7",
    displayName: "Employee Commuting",
    ghgProtocolId: "3.7",
    description: "Transportation of employees between their homes and their worksites during the reporting year",
    materialSectors: ["All sectors with significant workforce"],
    esrsRequirements: ["E1-6.57"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Survey-based or average data, include teleworking",
    examples: ["Personal vehicles", "Public transportation", "Company shuttles", "Remote work energy use"]
  },
  upstream_leased_assets: {
    id: "cat8",
    displayName: "Upstream Leased Assets",
    ghgProtocolId: "3.8",
    description: "Operation of assets leased by the reporting company (lessee) in the reporting year and not included in scope 1 and scope 2",
    materialSectors: ["Real Estate", "Retail", "Logistics"],
    esrsRequirements: ["E1-6.58"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Include if not in Scope 1/2",
    examples: ["Leased buildings", "Leased vehicles", "Leased equipment", "Data centers"]
  },
  downstream_transportation: {
    id: "cat9",
    displayName: "Downstream Transportation and Distribution",
    ghgProtocolId: "3.9",
    description: "Transportation and distribution of products sold by the reporting company in the reporting year between the reporting company's operations and the end consumer",
    materialSectors: ["Retail", "E-commerce", "Manufacturing"],
    esrsRequirements: ["E1-6.59"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Include where company doesn't pay",
    examples: ["Outbound logistics", "Retail distribution", "Customer pickup trips", "Home delivery"]
  },
  processing_sold_products: {
    id: "cat10",
    displayName: "Processing of Sold Products",
    ghgProtocolId: "3.10",
    description: "Processing of intermediate products sold in the reporting year by downstream companies",
    materialSectors: ["Chemicals", "Materials", "Components"],
    esrsRequirements: ["E1-6.60"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Estimate downstream processing energy",
    examples: ["Processing of sold materials", "Manufacturing with sold components", "Refining of sold products"]
  },
  use_of_sold_products: {
    id: "cat11",
    displayName: "Use of Sold Products",
    ghgProtocolId: "3.11",
    description: "End use of goods and services sold by the reporting company in the reporting year",
    materialSectors: ["Automotive", "Electronics", "Appliances", "Energy"],
    esrsRequirements: ["E1-6.61"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Calculate lifetime use-phase emissions",
    examples: ["Electricity consumption of sold products", "Fuel consumption of sold vehicles", "Direct emissions during use"]
  },
  end_of_life_treatment: {
    id: "cat12",
    displayName: "End-of-Life Treatment of Sold Products",
    ghgProtocolId: "3.12",
    description: "Waste disposal and treatment of products sold by the reporting company at the end of their life",
    materialSectors: ["Consumer Goods", "Electronics", "Automotive"],
    esrsRequirements: ["E1-6.62"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Model disposal pathways by material",
    examples: ["Landfilling", "Incineration", "Recycling", "Product take-back programs"]
  },
  downstream_leased_assets: {
    id: "cat13",
    displayName: "Downstream Leased Assets",
    ghgProtocolId: "3.13",
    description: "Operation of assets owned by the reporting company (lessor) and leased to other entities in the reporting year",
    materialSectors: ["Real Estate", "Equipment Rental", "Fleet Management"],
    esrsRequirements: ["E1-6.63"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Include lessee Scope 1&2",
    examples: ["Leased real estate", "Leased fleet vehicles", "Leased equipment", "Leased infrastructure"]
  },
  franchises: {
    id: "cat14",
    displayName: "Franchises",
    ghgProtocolId: "3.14",
    description: "Operation of franchises in the reporting year, not included in scope 1 and scope 2",
    materialSectors: ["Retail", "Food Service", "Hospitality"],
    esrsRequirements: ["E1-6.64"],
    cdpQuestions: ["C6.5"],
    calculationGuidance: "Include franchisee Scope 1&2",
    examples: ["Franchise locations", "Licensed operations", "Branded outlets"]
  },
  investments: {
    id: "cat15",
    displayName: "Investments",
    ghgProtocolId: "3.15",
    description: "Operation of investments in the reporting year, not included in scope 1 or scope 2",
    materialSectors: ["Finance", "Insurance", "Asset Management"],
    esrsRequirements: ["E1-6.65", "E1-6.66"],
    cdpQuestions: ["C6.5", "C-FS14.1"],
    calculationGuidance: "Apply PCAF methodology",
    examples: ["Equity investments", "Debt investments", "Project finance", "Joint ventures", "Subsidiaries"]
  }
} as const;

// Type definitions
export type Scope3CategoryKey = keyof typeof SCOPE3_CATEGORIES;
export type Scope3Category = typeof SCOPE3_CATEGORIES[Scope3CategoryKey];

// Helper functions for UI
export const getCategoryDisplayName = (categoryKey: string): string => {
  return SCOPE3_CATEGORIES[categoryKey as Scope3CategoryKey]?.displayName || categoryKey;
};

export const getCategoryTooltip = (categoryKey: string): string => {
  const category = SCOPE3_CATEGORIES[categoryKey as Scope3CategoryKey];
  return category ? `${category.description}\n\nExamples: ${category.examples.join(', ')}` : '';
};

export const getESRSRequirements = (categoryKey: string): readonly string[] => {
  return [...(SCOPE3_CATEGORIES[categoryKey as Scope3CategoryKey]?.esrsRequirements || [])];
};

export const getCDPQuestions = (categoryKey: string): string[] => {
  return [...(SCOPE3_CATEGORIES[categoryKey as Scope3CategoryKey]?.cdpQuestions || [])];
};

export const isMaterialForSector = (categoryKey: string, sector: string): boolean => {
  const category = SCOPE3_CATEGORIES[categoryKey as Scope3CategoryKey];
  return category ? ((category.materialSectors || []) as any as string[]).includes(sector) || ((category.materialSectors || []) as any as string[]).includes("All sectors") : false;
};

export const getCategoryGuidance = (categoryKey: string): string => {
  return SCOPE3_CATEGORIES[categoryKey as Scope3CategoryKey]?.calculationGuidance || "";
};

export const getAllCategories = (): Scope3CategoryKey[] => {
  return Object.keys(SCOPE3_CATEGORIES) as Scope3CategoryKey[];
};

export const getCategoriesBySector = (sector: string): Scope3CategoryKey[] => {
  return getAllCategories().filter(key => isMaterialForSector(key, sector));
};

// Materiality thresholds by sector (matching Python version)
export const MATERIALITY_THRESHOLDS = {
  Manufacturing: 0.05,
  Retail: 0.10,
  Technology: 0.03,
  Finance: 0.15,
  Energy: 0.08,
  Healthcare: 0.06,
  Transportation: 0.07,
  Default: 0.05,
} as const;

export type SectorType = keyof typeof MATERIALITY_THRESHOLDS;

export const getMaterialityThreshold = (sector: string): number => {
  return MATERIALITY_THRESHOLDS[sector as SectorType] || MATERIALITY_THRESHOLDS.Default;
};

// Category groupings for UI organization
export const CATEGORY_GROUPS = {
  "Upstream": [
    "purchased_goods_services",
    "capital_goods",
    "fuel_energy_activities",
    "upstream_transportation",
    "waste_operations",
    "business_travel",
    "employee_commuting",
    "upstream_leased_assets"
  ],
  "Downstream": [
    "downstream_transportation",
    "processing_sold_products",
    "use_of_sold_products",
    "end_of_life_treatment",
    "downstream_leased_assets"
  ],
  "Other": [
    "franchises",
    "investments"
  ]
} as const;

export type CategoryGroup = keyof typeof CATEGORY_GROUPS;

export const getCategoryGroup = (categoryKey: string): CategoryGroup | undefined => {
  for (const [group, categories] of Object.entries(CATEGORY_GROUPS)) {
    if ((categories as unknown as string[]).includes(categoryKey)) {
      return group as CategoryGroup;
    }
  }
  return undefined;
};
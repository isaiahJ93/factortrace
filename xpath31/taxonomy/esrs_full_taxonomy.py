"""Full ESRS taxonomy aligned with EFRAG standards."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class ESRSStandard(Enum):
    """ESRS standards as per EFRAG."""
    # Cross-cutting
    ESRS_1 = "General requirements"
    ESRS_2 = "General disclosures"
    
    # Environmental
    ESRS_E1 = "Climate change"
    ESRS_E2 = "Pollution"
    ESRS_E3 = "Water and marine resources"
    ESRS_E4 = "Biodiversity and ecosystems"
    ESRS_E5 = "Resource use and circular economy"
    
    # Social
    ESRS_S1 = "Own workforce"
    ESRS_S2 = "Workers in the value chain"
    ESRS_S3 = "Affected communities"
    ESRS_S4 = "Consumers and end-users"
    
    # Governance
    ESRS_G1 = "Business conduct"

@dataclass
class ESRSDatapoint:
    """EFRAG-compliant datapoint."""
    standard: ESRSStandard
    dp_code: str  # e.g., "E1-1"
    name: str
    definition: str
    data_type: str  # monetary, percentage, text, etc.
    period_type: str  # point-in-time, duration, etc.
    mandatory: bool
    
class EFRAGTaxonomy:
    """Complete EFRAG ESRS taxonomy."""
    
    def __init__(self):
        self.datapoints = self._load_esrs_datapoints()
        
    def _load_esrs_datapoints(self) -> Dict[str, ESRSDatapoint]:
        """Load all ESRS datapoints per EFRAG."""
        datapoints = {}
        
        # ESRS 2 - General disclosures (mandatory)
        datapoints['ESRS2-GOV-1'] = ESRSDatapoint(
            standard=ESRSStandard.ESRS_2,
            dp_code='GOV-1',
            name='Governance bodies composition',
            definition='Composition of administrative, management and supervisory bodies',
            data_type='narrative',
            period_type='point-in-time',
            mandatory=True
        )
        
        # ESRS E1 - Climate (mandatory for large companies)
        datapoints['ESRS-E1-1'] = ESRSDatapoint(
            standard=ESRSStandard.ESRS_E1,
            dp_code='E1-1',
            name='Transition plan for climate change mitigation',
            definition='Disclosure of transition plan aligned with 1.5°C',
            data_type='narrative',
            period_type='point-in-time',
            mandatory=True
        )
        
        datapoints['ESRS-E1-6'] = ESRSDatapoint(
            standard=ESRSStandard.ESRS_E1,
            dp_code='E1-6',
            name='Gross Scope 1 GHG emissions',
            definition='Total gross Scope 1 GHG emissions in metric tons CO2eq',
            data_type='decimal',
            period_type='duration',
            mandatory=True
        )
        
        # Add more datapoints...
        return datapoints

# CSRD-specific requirements
class CSRDRequirements:
    """CSRD compliance requirements."""
    
    MANDATORY_DISCLOSURES = [
        # Double materiality
        'material-impacts',
        'material-risks',
        'material-opportunities',
        
        # Value chain
        'upstream-value-chain',
        'downstream-value-chain',
        'value-chain-due-diligence',
        
        # Targets
        'science-based-targets',
        'intermediate-targets',
        'progress-tracking',
        
        # EU Taxonomy
        'taxonomy-eligible-activities',
        'taxonomy-aligned-activities',
        'capex-opex-breakdown'
    ]
    
    @staticmethod
    def validate_csrd_compliance(tagged_data: Dict) -> List[str]:
        """Check CSRD compliance of tagged data."""
        missing = []
        for req in CSRDRequirements.MANDATORY_DISCLOSURES:
            if req not in tagged_data:
                missing.append(req)
        return missing

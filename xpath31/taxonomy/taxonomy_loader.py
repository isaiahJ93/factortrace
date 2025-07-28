"""ESRS Taxonomy loader and manager."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import xml.etree.ElementTree as ET

@dataclass
class TaxonomyConcept:
    """Represents an XBRL taxonomy concept."""
    name: str
    label: str
    type: str
    period_type: str  # instant or duration
    balance: Optional[str] = None  # debit or credit
    abstract: bool = False
    nillable: bool = True
    
@dataclass 
class TaxonomySchema:
    """ESRS taxonomy schema."""
    namespace: str
    prefix: str
    concepts: Dict[str, TaxonomyConcept]
    
class ESRSTaxonomyLoader:
    """Load and manage ESRS taxonomies."""
    
    # ESRS concept patterns for auto-tagging
    CONCEPT_PATTERNS = {
        # E1 - Climate
        'ghg emissions scope 1': 'esrs-e1:GHGEmissionsScope1',
        'ghg emissions scope 2': 'esrs-e1:GHGEmissionsScope2', 
        'ghg emissions scope 3': 'esrs-e1:GHGEmissionsScope3Total',
        'scope 3 category 1': 'esrs-e1:GHGEmissionsScope3Cat01',
        'scope 3 category 2': 'esrs-e1:GHGEmissionsScope3Cat02',
        'purchased goods and services': 'esrs-e1:GHGEmissionsScope3Cat01',
        'capital goods': 'esrs-e1:GHGEmissionsScope3Cat02',
        
        # S1 - Own workforce
        'number of employees': 'esrs-s1:NumberOfEmployees',
        'gender pay gap': 'esrs-s1:GenderPayGap',
        'employee turnover': 'esrs-s1:EmployeeTurnoverRate',
        
        # G1 - Governance
        'board diversity': 'esrs-g1:BoardGenderDiversity',
        'whistleblowing cases': 'esrs-g1:WhistleblowingCases',
        'anti-corruption training': 'esrs-g1:AntiCorruptionTraining',
        
        # General
        'revenue': 'ifrs-full:Revenue',
        'total assets': 'ifrs-full:Assets',
        'net profit': 'ifrs-full:ProfitLoss',
    }
    
    def __init__(self, taxonomy_path: Optional[Path] = None):
        """Initialize with ESRS taxonomy."""
        self.schemas: Dict[str, TaxonomySchema] = {}
        self.concept_labels: Dict[str, str] = {}
        
        # Load default ESRS concepts
        self._load_default_concepts()
        
    def _load_default_concepts(self):
        """Load default ESRS taxonomy concepts."""
        # E1 - Climate concepts
        e1_concepts = {
            'GHGEmissionsScope1': TaxonomyConcept(
                name='GHGEmissionsScope1',
                label='GHG emissions Scope 1',
                type='xbrli:decimalItemType',
                period_type='duration'
            ),
            'GHGEmissionsScope2': TaxonomyConcept(
                name='GHGEmissionsScope2',
                label='GHG emissions Scope 2', 
                type='xbrli:decimalItemType',
                period_type='duration'
            ),
            'GHGEmissionsScope3Total': TaxonomyConcept(
                name='GHGEmissionsScope3Total',
                label='GHG emissions Scope 3 - Total',
                type='xbrli:decimalItemType',
                period_type='duration'
            ),
        }
        
        # Add Scope 3 categories
        for i in range(1, 16):
            e1_concepts[f'GHGEmissionsScope3Cat{i:02d}'] = TaxonomyConcept(
                name=f'GHGEmissionsScope3Cat{i:02d}',
                label=f'GHG emissions Scope 3 - Category {i}',
                type='xbrli:decimalItemType',
                period_type='duration'
            )
            
        self.schemas['esrs-e1'] = TaxonomySchema(
            namespace='http://www.esrs.eu/taxonomy/e1',
            prefix='esrs-e1',
            concepts=e1_concepts
        )
        
        # Build reverse label lookup
        for schema in self.schemas.values():
            for concept in schema.concepts.values():
                self.concept_labels[concept.label.lower()] = f"{schema.prefix}:{concept.name}"
                
    def find_concept_by_label(self, text: str) -> Optional[str]:
        """Find concept QName by label text."""
        text_lower = text.lower().strip()
        
        # Check exact match first
        if text_lower in self.concept_labels:
            return self.concept_labels[text_lower]
            
        # Check patterns
        for pattern, concept in self.CONCEPT_PATTERNS.items():
            if pattern in text_lower:
                return concept
                
        return None
        
    def get_concept(self, qname: str) -> Optional[TaxonomyConcept]:
        """Get concept by qualified name."""
        if ':' in qname:
            prefix, name = qname.split(':', 1)
            if prefix in self.schemas:
                return self.schemas[prefix].concepts.get(name)
        return None

    # Add CSRD-specific patterns
    CSRD_PATTERNS = {
        # Double materiality
        'material impact': 'esrs-2:MaterialImpacts',
        'material risk': 'esrs-2:MaterialRisks',
        'material opportunit': 'esrs-2:MaterialOpportunities',
        
        # Transition plans
        'transition plan': 'esrs-e1:TransitionPlan',
        'science-based target': 'esrs-e1:ScienceBasedTargets',
        'net-zero target': 'esrs-e1:NetZeroTarget',
        
        # EU Taxonomy
        'taxonomy eligible': 'eu-tax:EligibleActivities',
        'taxonomy aligned': 'eu-tax:AlignedActivities',
        
        # Value chain
        'value chain': 'esrs-2:ValueChainInformation',
        'due diligence': 'esrs-2:DueDiligenceProcess',
    }

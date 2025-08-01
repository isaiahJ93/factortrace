# esrs_validation.py
# Critical validation rules for ESRS E1 compliance

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

class ESRSValidator:
    """ESRS E1 Climate Change validation rules per EFRAG requirements"""
    
    @staticmethod
    def validate_lei(lei: str) -> Tuple[bool, Optional[str]]:
        """Validate Legal Entity Identifier format"""
        if not lei:
            return False, "LEI is mandatory for ESRS reporting"
        
        if not re.match(r'^[A-Z0-9]{20}$', lei):
            return False, "LEI must be 20 alphanumeric characters"
        
        # Check digit validation (ISO 17442)
        def char_to_num(c):
            return str(ord(c) - 55) if c.isalpha() else c
        
        lei_numeric = ''.join(char_to_num(c) for c in lei)
        check_digits = int(lei_numeric[-2:])
        base_number = lei_numeric[:-2]
        
        # Mod 97 calculation
        remainder = int(base_number) % 97
        calculated_check = 98 - remainder
        
        if calculated_check != check_digits:
            return False, "Invalid LEI check digits"
        
        return True, None
    
    @staticmethod
    def validate_nace_code(nace_code: str) -> Tuple[bool, Optional[str]]:
        """Validate NACE Rev. 2 code format"""
        if not nace_code:
            return False, "Primary NACE code is mandatory"
        
        if not re.match(r'^\d{2}\.\d{2}$', nace_code):
            return False, "NACE code must be in format XX.XX"
        
        # Valid NACE sections (A-U)
        section = int(nace_code.split('.')[0])
        if section < 1 or section > 99:
            return False, "Invalid NACE section code"
        
        return True, None
    
    @staticmethod
    def validate_ghg_emissions(data: Dict) -> List[str]:
        """Validate GHG emissions data per ESRS E1-6"""
        errors = []
        
        # Required emission scopes
        if data.get('scope1_total', 0) < 0:
            errors.append("Scope 1 emissions cannot be negative")
        
        if data.get('scope2_location', 0) < 0:
            errors.append("Scope 2 location-based emissions cannot be negative")
        
        # Market-based cannot exceed location-based
        if data.get('scope2_market', 0) > data.get('scope2_location', 0):
            errors.append("Scope 2 market-based cannot exceed location-based emissions")
        
        # Validate Scope 3 categories sum
        if 'scope3_categories' in data and data.get('scope3_total'):
            categories_sum = sum(data['scope3_categories'].values())
            if abs(categories_sum - data['scope3_total']) > 0.01:
                errors.append(f"Scope 3 categories ({categories_sum}) must sum to total ({data['scope3_total']})")
        
        # Validate GHG breakdown
        if 'ghg_breakdown' in data:
            ghg_sum = sum(data['ghg_breakdown'].values())
            total = data.get('total_ghg_emissions', 0)
            if abs(ghg_sum - total) > 0.01:
                errors.append(f"GHG breakdown ({ghg_sum}) must sum to total emissions ({total})")
        
        # Validate total emissions
        expected_total = (
            data.get('scope1_total', 0) + 
            data.get('scope2_location', 0) + 
            data.get('scope3_total', 0)
        )
        if abs(data.get('total_ghg_emissions', 0) - expected_total) > 0.01:
            errors.append("Total emissions must equal sum of Scope 1, 2, and 3")
        
        return errors
    
    @staticmethod
    def validate_transition_plan(data: Dict) -> List[str]:
        """Validate transition plan per ESRS E1-1"""
        errors = []
        
        if not data.get('has_transition_plan'):
            return errors  # No plan is valid, just needs disclosure
        
        # If has plan, validate requirements
        if data.get('aligned_1_5c') and not data.get('science_based_targets'):
            errors.append("1.5°C alignment claims require science-based targets")
        
        target_year = data.get('net_zero_target_year')
        if target_year:
            current_year = datetime.now().year
            if target_year < current_year:
                errors.append("Net-zero target year cannot be in the past")
            if target_year > 2070:
                errors.append("Net-zero target year seems unrealistic (>2070)")
        
        return errors
    
    @staticmethod
    def validate_targets(data: Dict) -> List[str]:
        """Validate emission reduction targets per ESRS E1-4"""
        errors = []
        
        for target in data.get('absolute_targets', []):
            if target['target_year'] <= target['base_year']:
                errors.append("Target year must be after base year")
            
            if target['target_reduction_percent'] <= 0:
                errors.append("Reduction percentage must be positive")
            
            if target['target_reduction_percent'] > 100:
                errors.append("Reduction percentage cannot exceed 100%")
            
            if not target.get('scopes_covered'):
                errors.append("Targets must specify which scopes are covered")
        
        return errors
    
    @staticmethod
    def validate_esrs_data(data: Dict) -> Tuple[bool, List[str]]:
        """Complete ESRS E1 validation"""
        all_errors = []
        
        # Entity validation
        lei_valid, lei_error = ESRSValidator.validate_lei(
            data.get('entity', {}).get('lei', '')
        )
        if not lei_valid:
            all_errors.append(lei_error)
        
        nace_valid, nace_error = ESRSValidator.validate_nace_code(
            data.get('entity', {}).get('primary_nace_code', '')
        )
        if not nace_valid:
            all_errors.append(nace_error)
        
        # Climate data validation
        climate_data = data.get('climate_change', {})
        
        all_errors.extend(
            ESRSValidator.validate_ghg_emissions(
                climate_data.get('ghg_emissions', {})
            )
        )
        
        all_errors.extend(
            ESRSValidator.validate_transition_plan(
                climate_data.get('transition_plan', {})
            )
        )
        
        all_errors.extend(
            ESRSValidator.validate_targets(
                climate_data.get('targets', {})
            )
        )
        
        # Period validation
        period = data.get('period', {})
        if not period.get('start_date') or not period.get('end_date'):
            all_errors.append("Reporting period dates are mandatory")
        
        return len(all_errors) == 0, all_errors


# XBRL-specific validations
class XBRLValidator:
    """XBRL 2.1 and iXBRL validation for EFRAG taxonomy"""
    
    @staticmethod
    def validate_context_ref(context_id: str, fact_value: any) -> bool:
        """Validate context references match fact types"""
        # Instant vs duration contexts
        if '_instant' in context_id and isinstance(fact_value, dict):
            return False  # Instant contexts for point-in-time values only
        
        if '_duration' in context_id and isinstance(fact_value, (int, float)):
            return True  # Duration contexts for flow values
        
        return True
    
    @staticmethod
    def validate_unit_ref(unit_id: str, fact_value: float) -> bool:
        """Validate unit references for numeric facts"""
        unit_mappings = {
            'tonnes_co2e': ['ghg_emissions', 'scope1', 'scope2', 'scope3'],
            'pure': ['percentages', 'ratios'],
            'euro': ['monetary_values'],
        }
        
        # Check if unit matches fact type
        return True  # Implement based on your taxonomy
    
    @staticmethod
    def validate_dimensions(fact: Dict) -> List[str]:
        """Validate dimensional information"""
        errors = []
        
        required_dims = {
            'ghg_emissions': ['ghg:GhgScopeAxis', 'ghg:GhgGasTypeAxis'],
            'targets': ['esrs:TargetTypeAxis', 'esrs:TimeHorizonAxis'],
        }
        
        # Implement dimension validation
        return errors
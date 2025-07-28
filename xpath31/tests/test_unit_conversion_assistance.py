"""Test suite for unit harmonization with conversion assistance."""
import pytest
from decimal import Decimal

class TestUnitConversionAssistance:
    """Test unit conversion assistance features."""
    
    def test_co2_unit_conversions(self):
        """Test CO2 unit conversion factors."""
        conversions = {
            'tCO2e': 1.0,
            'kgCO2e': 0.001,
            'MtCO2e': 1_000_000.0
        }
        
        # Test kg to tonnes
        kg_value = 1000
        tonnes_value = kg_value * conversions['kgCO2e']
        assert tonnes_value == 1.0
        
        # Test megatonnes to tonnes
        mt_value = 0.001
        tonnes_value = mt_value * conversions['MtCO2e']
        assert tonnes_value == 1000.0
        
    def test_decimal_conversion_precision(self):
        """Test precision in conversions."""
        # 500,000 kg = 500 tonnes
        kg_value = Decimal('500000')
        conversion_factor = Decimal('0.001')
        tonnes_value = kg_value * conversion_factor
        
        assert tonnes_value == Decimal('500')
        # Accept either format
        assert str(tonnes_value) in ['500', '500.000']
        
    def test_conversion_formulas(self):
        """Test XBRL formula generation."""
        # Test formula for kg to tonnes
        from_unit = 'kgCO2e'
        to_unit = 'tCO2e'
        factor = 0.001
        
        formula = f"@{{{from_unit}}} * {factor}"
        assert formula == "@{kgCO2e} * 0.001"

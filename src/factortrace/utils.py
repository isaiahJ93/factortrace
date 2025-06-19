import uuid
from datetime import datetime
import hashlib
import json


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def hash_voucher_dict(voucher: dict) -> str:
    # Remove the hash key if it's already present
    copy = dict(voucher)
    copy.pop("hash", None)
    serialized = json.dumps(copy, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Any, Dict
import json

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as etree
    LXML_AVAILABLE = False


def add_to_xml_method(EmissionVoucherClass):
    """Decorator to add to_xml method to EmissionVoucher Pydantic model"""
    
    def to_xml(self) -> str:
        """
        Serialize EmissionVoucher to ESRS E1/CBAM compliant XML.
        
        Returns:
            str: Pretty-printed XML string (UTF-8 encoded)
        """
        # Create root element with namespace
        root = etree.Element(
            "{urn:iso:std:20022:tech:xsd:esrs.e1.001.01}EmissionVoucher",
            nsmap={
                None: "urn:iso:std:20022:tech:xsd:esrs.e1.001.01",
                "cbam": "urn:eu:cbam:xsd:declaration:001.01"
            } if LXML_AVAILABLE else None
        )
        
        if not LXML_AVAILABLE:
            # ElementTree fallback: set namespace manually
            root.set("xmlns", "urn:iso:std:20022:tech:xsd:esrs.e1.001.01")
            root.set("xmlns:cbam", "urn:eu:cbam:xsd:declaration:001.01")
        
        root.set("version", "1.0.0")
        
        # Header section
        header = etree.SubElement(root, "Header")
        _add_if_not_none(header, "VoucherId", self.voucher_id)
        _add_if_not_none(header, "CreationDateTime", _format_datetime(self.creation_datetime))
        _add_if_not_none(header, "SubmissionDateTime", _format_datetime(self.submission_datetime))
        _add_if_not_none(header, "MessageType", self.message_type or "ORIGINAL")
        _add_if_not_none(header, "PreviousVoucherId", self.previous_voucher_id)
        
        # Reporting Entity
        entity = etree.SubElement(root, "ReportingEntity")
        _add_if_not_none(entity, "LEI", self.reporting_entity_lei)
        _add_if_not_none(entity, "Name", self.reporting_entity_name)
        _add_if_not_none(entity, "JurisdictionCountry", self.reporting_entity_country)
        
        # Supplier
        supplier = etree.SubElement(root, "Supplier")
        _add_if_not_none(supplier, "Id", self.supplier_id)
        _add_if_not_none(supplier, "Name", self.supplier_name)
        _add_if_not_none(supplier, "LEI", self.supplier_lei)
        _add_if_not_none(supplier, "Country", self.supplier_country)
        _add_if_not_none(supplier, "TaxId", self.supplier_tax_id)
        
        # Product
        product = etree.SubElement(root, "Product")
        _add_if_not_none(product, "CNCode", self.product_cn_code)
        _add_if_not_none(product, "Description", self.product_description)
        _add_if_not_none(product, "Category", self.product_category)
        _add_if_not_none(product, "MaterialType", self.material_type)
        
        # Installation (optional)
        if hasattr(self, 'installation') and self.installation:
            inst = etree.SubElement(root, "Installation")
            _add_if_not_none(inst, "InstallationId", self.installation.installation_id)
            _add_if_not_none(inst, "Name", self.installation.name)
            _add_if_not_none(inst, "Country", self.installation.country)
            _add_if_not_none(inst, "Address", self.installation.address)
            
            if hasattr(self.installation, 'coordinates') and self.installation.coordinates:
                coords = etree.SubElement(inst, "Coordinates")
                _add_if_not_none(coords, "Latitude", self.installation.coordinates.latitude)
                _add_if_not_none(coords, "Longitude", self.installation.coordinates.longitude)
        
        # Activity Data
        activity = etree.SubElement(root, "ActivityData")
        quantity = etree.SubElement(activity, "Quantity")
        quantity.text = str(self.activity_quantity)
        quantity.set("unit", self.activity_quantity_unit)
        
        monetary = etree.SubElement(activity, "MonetaryValue")
        monetary.text = str(self.monetary_value)
        monetary.set("currency", self.currency)
        
        _add_if_not_none(activity, "ActivityDescription", self.activity_description)
        
        # Emission Data
        emissions = etree.SubElement(root, "EmissionData")
        _add_if_not_none(emissions, "Scope", self.emission_scope)
        _add_if_not_none(emissions, "Scope3Category", self.scope3_category)
        
        direct = etree.SubElement(emissions, "DirectEmissions")
        direct.text = str(self.direct_emissions)
        direct.set("unit", self.emission_unit or "tCO2e")
        
        if self.indirect_emissions is not None:
            indirect = etree.SubElement(emissions, "IndirectEmissions")
            indirect.text = str(self.indirect_emissions)
            indirect.set("unit", self.emission_unit or "tCO2e")
        
        if self.biogenic_emissions is not None:
            biogenic = etree.SubElement(emissions, "BiogenicEmissions")
            biogenic.text = str(self.biogenic_emissions)
            biogenic.set("unit", self.emission_unit or "tCO2e")
        
        # GHG Breakdown
        if hasattr(self, 'ghg_breakdown') and self.ghg_breakdown:
            breakdown = etree.SubElement(emissions, "GHGBreakdown")
            _add_emission_amount(breakdown, "CO2", self.ghg_breakdown.co2)
            _add_emission_amount(breakdown, "CH4", self.ghg_breakdown.ch4)
            _add_emission_amount(breakdown, "N2O", self.ghg_breakdown.n2o)
            _add_emission_amount(breakdown, "HFCs", self.ghg_breakdown.hfcs)
            _add_emission_amount(breakdown, "PFCs", self.ghg_breakdown.pfcs)
            _add_emission_amount(breakdown, "SF6", self.ghg_breakdown.sf6)
            _add_emission_amount(breakdown, "NF3", self.ghg_breakdown.nf3)
            _add_emission_amount(breakdown, "Total", self.ghg_breakdown.total)
        
        # Emission Factor
        factor = etree.SubElement(emissions, "EmissionFactor")
        _add_if_not_none(factor, "FactorId", self.emission_factor_id)
        _add_if_not_none(factor, "Value", self.emission_factor_value)
        _add_if_not_none(factor, "Unit", self.emission_factor_unit)
        _add_if_not_none(factor, "Source", self.emission_factor_source)
        _add_if_not_none(factor, "SourceReference", self.emission_factor_source_ref)
        _add_if_not_none(factor, "ValidFrom", _format_date(self.emission_factor_valid_from))
        _add_if_not_none(factor, "IsDefault", str(self.emission_factor_is_default).lower())
        
        # Calculation Method
        method = etree.SubElement(emissions, "CalculationMethod")
        _add_if_not_none(method, "Method", self.calculation_method)
        _add_if_not_none(method, "Description", self.calculation_description)
        _add_if_not_none(method, "Standard", self.calculation_standard)
        
        if self.carbon_price_paid is not None:
            carbon_price = etree.SubElement(emissions, "CarbonPricePaid")
            carbon_price.text = str(self.carbon_price_paid)
            carbon_price.set("currency", self.currency)
        
        # Reporting Period
        period = etree.SubElement(root, "ReportingPeriod")
        _add_if_not_none(period, "StartDate", _format_date(self.reporting_start_date))
        _add_if_not_none(period, "EndDate", _format_date(self.reporting_end_date))
        _add_if_not_none(period, "ReportingYear", str(self.reporting_year))
        
        # Data Quality
        quality = etree.SubElement(root, "DataQuality")
        _add_if_not_none(quality, "QualityScore", str(self.data_quality_score))
        _add_if_not_none(quality, "DataSource", self.data_source)
        
        if hasattr(self, 'uncertainty_assessment') and self.uncertainty_assessment:
            uncertainty = etree.SubElement(quality, "UncertaintyAssessment")
            _add_if_not_none(uncertainty, "UncertaintyPercentage", self.uncertainty_assessment.percentage)
            _add_if_not_none(uncertainty, "ConfidenceLevel", self.uncertainty_assessment.confidence_level or 95)
            _add_if_not_none(uncertainty, "Method", self.uncertainty_assessment.method)
        
        _add_if_not_none(quality, "PrimaryDataPercentage", self.primary_data_percentage)
        
        # Verification
        verification = etree.SubElement(root, "Verification")
        _add_if_not_none(verification, "CalculationHash", self.calculation_hash)
        _add_if_not_none(verification, "HashAlgorithm", self.hash_algorithm or "SHA-256")
        
        if hasattr(self, 'third_party_verification') and self.third_party_verification:
            tpv = etree.SubElement(verification, "ThirdPartyVerification")
            _add_if_not_none(tpv, "VerifierId", self.third_party_verification.verifier_id)
            _add_if_not_none(tpv, "AccreditationNumber", self.third_party_verification.accreditation_number)
            _add_if_not_none(tpv, "VerificationDate", _format_date(self.third_party_verification.verification_date))
            _add_if_not_none(tpv, "VerificationLevel", self.third_party_verification.verification_level)
        
        # Convert to string with pretty printing
        if LXML_AVAILABLE:
            return etree.tostring(
                root, 
                pretty_print=True, 
                xml_declaration=True, 
                encoding='UTF-8'
            ).decode('utf-8')
        else:
            # ElementTree fallback
            etree.indent(root, space='  ')
            return etree.tostring(
                root, 
                encoding='unicode', 
                xml_declaration=True
            )
    
    # Attach method to class
    EmissionVoucherClass.to_xml = to_xml
    return EmissionVoucherClass


def _add_if_not_none(parent: etree.Element, tag: str, value: Any) -> Optional[etree.Element]:
    """Add child element only if value is not None"""
    if value is not None:
        elem = etree.SubElement(parent, tag)
        if isinstance(value, (Decimal, float, int)):
            elem.text = str(value)
        elif isinstance(value, bool):
            elem.text = str(value).lower()
        else:
            elem.text = str(value)
        return elem
    return None


def _add_emission_amount(parent: etree.Element, tag: str, value: Optional[Decimal]) -> Optional[etree.Element]:
    """Add emission amount element with unit attribute"""
    if value is not None:
        elem = etree.SubElement(parent, tag)
        elem.text = str(value)
        elem.set("unit", "tCO2e")
        return elem
    return None


def _format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO 8601 with timezone"""
    if dt is None:
        return None
    return dt.isoformat()


def _format_date(d: Optional[date]) -> Optional[str]:
    """Format date to ISO 8601"""
    if d is None:
        return None
    return d.isoformat()


def validate_against_xsd(xml_string: str, xsd_path: str) -> tuple[bool, List[str]]:
    """
    Validate XML against XSD schema
    
    Args:
        xml_string: XML document as string
        xsd_path: Path to XSD schema file
        
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    if not LXML_AVAILABLE:
        return True, ["XSD validation requires lxml library"]
    
    try:
        # Parse XSD
        with open(xsd_path, 'r') as f:
            xsd_doc = etree.parse(f)
        schema = etree.XMLSchema(xsd_doc)
        
        # Parse XML
        xml_doc = etree.fromstring(xml_string.encode('utf-8'))
        
        # Validate
        is_valid = schema.validate(xml_doc)
        errors = [str(e) for e in schema.error_log]
        
        return is_valid, errors
    except Exception as e:
        return False, [f"Validation error: {str(e)}"]


# Usage example:
# @add_to_xml_method
# class EmissionVoucher(BaseModel):
#     # ... your Pydantic fields ...
#     pass
#
# voucher = EmissionVoucher(**SAMPLE_DATA)
# xml_str = voucher.to_xml()
# print(xml_str)
#
# # Optional: validate against XSD
# is_valid, errors = validate_against_xsd(xml_str, "voucher.xsd")
# if not is_valid:
#     print("Validation errors:", errors)
```

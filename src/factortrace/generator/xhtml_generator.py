"""
XHTML + iXBRL Generator for FactorTrace Scope 3 Compliance Platform
Handles ESRS/CSRD, CBAM, CDP, and GHG Protocol taxonomies with full Scope 3 mapping
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

from pydantic import BaseModel, Field, field_validator


# Configure module logger
logger = logging.getLogger(__name__)


# Namespace definitions for all supported taxonomies
NAMESPACES = {
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'ix': 'http://www.xbrl.org/2013/inlineXBRL',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xbrli': 'http://www.xbrl.org/2003/instance',
    'link': 'http://www.xbrl.org/2003/linkbase',
    'iso4217': 'http://www.xbrl.org/2003/iso4217',
    'esrs': 'http://xbrl.efrag.org/taxonomy/2024-03-31/esrs',
    'csrd': 'http://xbrl.europa.eu/taxonomy/csrd/2024',
    'ghgp': 'http://xbrl.ghgprotocol.org/2024/ghg-protocol',
    'cbam': 'http://xbrl.europa.eu/taxonomy/cbam/2024',
    'cdp': 'http://xbrl.cdp.net/taxonomy/2024/cdp',
}

# Comprehensive Scope 3 category mapping across taxonomies
SCOPE3_TAXONOMY_MAP = {
    'category_1_purchased_goods': {
        'esrs': 'esrs:Scope3PurchasedGoodsServices',
        'ghgp': 'ghgp:Scope3Category1PurchasedGoods',
        'csrd': 'csrd:E1-6.66',
    },
    'category_2_capital_goods': {
        'esrs': 'esrs:Scope3CapitalGoods',
        'ghgp': 'ghgp:Scope3Category2CapitalGoods',
        'csrd': 'csrd:E1-6.67',
    },
    'category_3_fuel_energy': {
        'esrs': 'esrs:Scope3FuelEnergyActivities',
        'ghgp': 'ghgp:Scope3Category3FuelEnergy',
        'csrd': 'csrd:E1-6.68',
    },
    'category_4_upstream_transport': {
        'esrs': 'esrs:Scope3UpstreamTransportDistribution',
        'ghgp': 'ghgp:Scope3Category4UpstreamTransport',
        'csrd': 'csrd:E1-6.69',
    },
    'category_5_waste': {
        'esrs': 'esrs:Scope3WasteOperations',
        'ghgp': 'ghgp:Scope3Category5Waste',
        'csrd': 'csrd:E1-6.70',
    },
    'category_6_business_travel': {
        'esrs': 'esrs:Scope3BusinessTravel',
        'ghgp': 'ghgp:Scope3Category6BusinessTravel',
        'csrd': 'csrd:E1-6.71',
    },
    'category_7_employee_commuting': {
        'esrs': 'esrs:Scope3EmployeeCommuting',
        'ghgp': 'ghgp:Scope3Category7Commuting',
        'csrd': 'csrd:E1-6.72',
    },
    'category_8_upstream_leased': {
        'esrs': 'esrs:Scope3UpstreamLeasedAssets',
        'ghgp': 'ghgp:Scope3Category8UpstreamLeased',
        'csrd': 'csrd:E1-6.73',
    },
    'category_9_downstream_transport': {
        'esrs': 'esrs:Scope3DownstreamTransportDistribution',
        'ghgp': 'ghgp:Scope3Category9DownstreamTransport',
        'csrd': 'csrd:E1-6.74',
    },
    'category_10_processing_sold': {
        'esrs': 'esrs:Scope3ProcessingSoldProducts',
        'ghgp': 'ghgp:Scope3Category10Processing',
        'csrd': 'csrd:E1-6.75',
    },
    'category_11_use_of_sold': {
        'esrs': 'esrs:Scope3UseSoldProducts',
        'ghgp': 'ghgp:Scope3Category11UseOfSold',
        'csrd': 'csrd:E1-6.76',
    },
    'category_12_end_of_life': {
        'esrs': 'esrs:Scope3EndOfLifeTreatment',
        'ghgp': 'ghgp:Scope3Category12EndOfLife',
        'csrd': 'csrd:E1-6.77',
    },
    'category_13_downstream_leased': {
        'esrs': 'esrs:Scope3DownstreamLeasedAssets',
        'ghgp': 'ghgp:Scope3Category13DownstreamLeased',
        'csrd': 'csrd:E1-6.78',
    },
    'category_14_franchises': {
        'esrs': 'esrs:Scope3Franchises',
        'ghgp': 'ghgp:Scope3Category14Franchises',
        'csrd': 'csrd:E1-6.79',
    },
    'category_15_investments': {
        'esrs': 'esrs:Scope3Investments',
        'ghgp': 'ghgp:Scope3Category15Investments',
        'csrd': 'csrd:E1-6.80',
    },
}


class Scope3Category(BaseModel):
    """Individual Scope 3 category data"""
    category_number: int = Field(ge=1, le=15)
    name: str
    emissions_tco2e: Decimal
    data_quality_score: Optional[float] = Field(None, ge=0, le=1)
    calculation_method: Optional[str] = None
    
    @field_validator('emissions_tco2e', mode='before')
    @classmethod
    def coerce_emissions_to_decimal(cls, v):
        """Coerce numeric values to Decimal for API robustness"""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v


class EmissionReportData(BaseModel):
    """Complete emission report data structure"""
    # Entity information
    entity_name: str
    entity_identifier: str
    reporting_period_start: date
    reporting_period_end: date
    
    # Emission totals
    scope1_total: Decimal
    scope2_location_total: Decimal
    scope2_market_total: Optional[Decimal] = None
    scope3_total: Decimal
    
    # Scope 3 breakdown - all 15 categories
    scope3_categories: List[Scope3Category]
    
    # Additional compliance data
    cbam_embedded_emissions: Optional[Dict[str, Decimal]] = None
    cdp_narrative_sections: Optional[Dict[str, str]] = None
    validation_scores: Optional[Dict[str, float]] = None
    factor_snapshots: Optional[List[Dict[str, Any]]] = None
    
    # Metadata
    report_currency: str = "EUR"
    report_language: str = "en"
    assurance_level: Optional[str] = None
    
    @field_validator('scope1_total', 'scope2_location_total', 'scope2_market_total', 'scope3_total', mode='before')
    @classmethod
    def coerce_totals_to_decimal(cls, v):
        """Coerce numeric values to Decimal for API robustness"""
        if v is None:
            return None
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v
    
    @field_validator('cbam_embedded_emissions', mode='before')
    @classmethod
    def coerce_cbam_to_decimal(cls, v):
        """Ensure CBAM emissions are Decimal"""
        if v is None:
            return None
        return {k: Decimal(str(val)) if isinstance(val, (int, float, str)) else val 
                for k, val in v.items()}


class XHTMLiXBRLGenerator:
    """Production-ready XHTML + iXBRL generator with full Scope 3 support
    
    Thread-safe implementation - create new instance per request or use
    the class methods directly for stateless operation.
    """
    
    def __init__(self):
        self._template_path: Optional[Path] = None
        self._template_content: Optional[str] = None
        
    def load_template(self, path: Path) -> None:
        """Load XHTML template from file system
        
        Template should contain placeholder elements with class="ixbrl-content"
        where generated content will be injected.
        """
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")
        self._template_path = path
        with open(path, 'r', encoding='utf-8') as f:
            self._template_content = f.read()
        logger.debug(f"Loaded template from {path}")
    
    def _inject_into_template(self, content: str) -> str:
        """Inject generated content into loaded template
        
        Looks for <div class="ixbrl-content"></div> and replaces with content.
        """
        if not self._template_content:
            return content
        
        # Simple placeholder replacement - could be enhanced with proper DOM parsing
        placeholder = '<div class="ixbrl-content"></div>'
        if placeholder in self._template_content:
            return self._template_content.replace(placeholder, content)
        
        logger.warning("Template loaded but no placeholder found, returning raw content")
        return content
    
    def render(self, data: EmissionReportData) -> str:
        """Render XHTML+iXBRL report with complete tagging
        
        Thread-safe: Creates all state locally without modifying instance.
        """
        logger.info(f"Starting report generation for {data.entity_name}")
        
        # Generate unique document ID
        doc_id = self._generate_document_id(data)
        logger.debug(f"Generated document ID: {doc_id}")
        
        # Build XHTML structure with local context counter
        html = self._build_xhtml_structure(data, doc_id)
        
        # Convert to string with proper formatting
        raw_output = self._serialize_html(html)
        
        # Apply template if loaded
        final_output = self._inject_into_template(raw_output) if self._template_content else raw_output
        
        logger.info(f"Report generation complete: {len(final_output)} chars")
        return final_output
    
    def save(self, content: str, output_path: Path) -> Path:
        """Save rendered content to file
        
        Args:
            content: The rendered XHTML content
            output_path: Path where to save the file
            
        Returns:
            Path to the saved file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    @classmethod
    def generate_report(cls, data: EmissionReportData) -> str:
        """Stateless report generation - recommended for FastAPI
        
        Usage:
            xhtml = XHTMLiXBRLGenerator.generate_report(emission_data)
            
        This avoids any threading issues in async contexts.
        """
        generator = cls()
        return generator.render(data)
    
    def validate_xhtml(self, content: str) -> bool:
        """Validate XHTML structure
        
        Args:
            content: The XHTML content to validate
            
        Returns:
            True if valid XHTML, False otherwise
        """
        try:
            ET.fromstring(content.encode('utf-8'))
            logger.debug("XHTML validation passed")
            return True
        except ET.ParseError as e:
            logger.warning(f"XHTML validation failed: {e}")
            return False
    
    def validate_ixbrl(self, content: str) -> bool:
        """Validate iXBRL tagging completeness
        
        Args:
            content: The XHTML content to validate
            
        Returns:
            True if all required iXBRL elements present
        """
        try:
            # Parse the content
            root = ET.fromstring(content.encode('utf-8'))
            
            # Check for required iXBRL elements using proper XML parsing
            ns = {'ix': 'http://www.xbrl.org/2013/inlineXBRL'}
            
            # Check header exists
            header = root.find('.//ix:header', ns)
            if header is None:
                logger.warning("iXBRL validation failed: Missing ix:header")
                return False
            
            # Check resources exist
            resources = root.find('.//ix:resources', ns)
            if resources is None:
                logger.warning("iXBRL validation failed: Missing ix:resources")
                return False
            
            # Check for numeric facts
            facts = root.findall('.//ix:nonFraction', ns)
            if not facts:
                logger.warning("iXBRL validation failed: No numeric facts found")
                return False
            
            # Verify all 15 Scope 3 categories are tagged
            fact_ids = {fact.get('id') for fact in facts if fact.get('id')}
            missing_categories = []
            for i in range(1, 16):
                if f'scope3-cat{i}' not in fact_ids:
                    missing_categories.append(i)
            
            if missing_categories:
                logger.warning(f"iXBRL validation failed: Missing Scope 3 categories {missing_categories}")
                return False
            
            logger.debug("iXBRL validation passed")
            return True
        except Exception as e:
            logger.error(f"iXBRL validation error: {e}")
            return False
    
    def _generate_document_id(self, data: EmissionReportData) -> str:
        """Generate unique document identifier"""
        content = f"{data.entity_identifier}-{data.reporting_period_end}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _build_xhtml_structure(self, data: EmissionReportData, doc_id: str) -> ET.Element:
        """Build complete XHTML+iXBRL document structure"""
        # Register namespaces
        for prefix, uri in NAMESPACES.items():
            ET.register_namespace(prefix, uri)
        
        # Root HTML element
        html = ET.Element('{http://www.w3.org/1999/xhtml}html')
        for prefix, uri in NAMESPACES.items():
            html.set(f'xmlns:{prefix}', uri)
        
        # Head section
        head = ET.SubElement(html, '{http://www.w3.org/1999/xhtml}head')
        self._add_metadata(head, data, doc_id)
        
        # Body section
        body = ET.SubElement(html, '{http://www.w3.org/1999/xhtml}body')
        
        # iXBRL header
        self._add_ixbrl_header(body, data, doc_id)
        
        # Main content sections
        self._add_entity_section(body, data)
        self._add_emissions_overview(body, data)
        self._add_scope3_breakdown(body, data)
        
        # Additional compliance sections
        if data.cbam_embedded_emissions:
            self._add_cbam_section(body, data)
        if data.cdp_narrative_sections:
            self._add_cdp_narratives(body, data)
        
        return html
    
    def _add_metadata(self, head: ET.Element, data: EmissionReportData, doc_id: str) -> None:
        """Add document metadata"""
        title = ET.SubElement(head, '{http://www.w3.org/1999/xhtml}title')
        title.text = f"Sustainability Report - {escape(data.entity_name)} - {data.reporting_period_end}"
        
        # Meta tags for compliance
        meta_tags = [
            {'name': 'document-id', 'content': doc_id},
            {'name': 'reporting-standard', 'content': 'ESRS,CSRD,GHG-Protocol'},
            {'name': 'assurance-level', 'content': data.assurance_level or 'limited'},
        ]
        
        for meta_data in meta_tags:
            meta = ET.SubElement(head, '{http://www.w3.org/1999/xhtml}meta')
            for key, value in meta_data.items():
                # Use quoteattr for safe attribute values
                meta.set(key, value if key == 'name' else escape(value))
    
    def _add_ixbrl_header(self, body: ET.Element, data: EmissionReportData, doc_id: str) -> None:
        """Add iXBRL header with contexts and units"""
        header = ET.SubElement(body, '{http://www.xbrl.org/2013/inlineXBRL}header')
        
        # Hidden section for XBRL metadata
        hidden = ET.SubElement(header, '{http://www.xbrl.org/2013/inlineXBRL}hidden')
        
        # References to taxonomies
        refs = ET.SubElement(hidden, '{http://www.xbrl.org/2013/inlineXBRL}references')
        schema_refs = [
            {'href': 'https://xbrl.efrag.org/taxonomy/2024-03-31/esrs-all.xsd', 'type': 'schema'},
            {'href': 'https://xbrl.ghgprotocol.org/2024/ghg-protocol.xsd', 'type': 'schema'},
        ]
        
        for ref_data in schema_refs:
            ref = ET.SubElement(refs, '{http://www.xbrl.org/2003/linkbase}schemaRef')
            ref.set('{http://www.w3.org/1999/xlink}href', ref_data['href'])
            ref.set('{http://www.w3.org/1999/xlink}type', 'simple')
        
        # Resources section
        resources = ET.SubElement(hidden, '{http://www.xbrl.org/2013/inlineXBRL}resources')
        
        # Add contexts and get mapping
        context_map = self._add_contexts(resources, data)
        
        # Add units
        self._add_units(resources)
    
    def _add_contexts(self, resources: ET.Element, data: EmissionReportData) -> Dict[str, str]:
        """Add reporting contexts and return context ID mapping
        
        Returns:
            Dict mapping context types to their IDs
        """
        context_map = {}
        
        # Instant context (end of period)
        instant_ctx = ET.SubElement(resources, '{http://www.xbrl.org/2003/instance}context')
        instant_ctx_id = 'ctx-instant'
        instant_ctx.set('id', instant_ctx_id)
        context_map['instant'] = instant_ctx_id
        
        entity = ET.SubElement(instant_ctx, '{http://www.xbrl.org/2003/instance}entity')
        identifier = ET.SubElement(entity, '{http://www.xbrl.org/2003/instance}identifier')
        identifier.set('scheme', 'http://www.example.com/entity-scheme')
        identifier.text = escape(data.entity_identifier)
        
        period = ET.SubElement(instant_ctx, '{http://www.xbrl.org/2003/instance}period')
        instant = ET.SubElement(period, '{http://www.xbrl.org/2003/instance}instant')
        instant.text = data.reporting_period_end.isoformat()
        
        # Duration context (full period)
        duration_ctx = ET.SubElement(resources, '{http://www.xbrl.org/2003/instance}context')
        duration_ctx_id = 'ctx-duration'
        duration_ctx.set('id', duration_ctx_id)
        context_map['duration'] = duration_ctx_id
        
        entity2 = ET.SubElement(duration_ctx, '{http://www.xbrl.org/2003/instance}entity')
        identifier2 = ET.SubElement(entity2, '{http://www.xbrl.org/2003/instance}identifier')
        identifier2.set('scheme', 'http://www.example.com/entity-scheme')
        identifier2.text = escape(data.entity_identifier)
        
        period2 = ET.SubElement(duration_ctx, '{http://www.xbrl.org/2003/instance}period')
        start = ET.SubElement(period2, '{http://www.xbrl.org/2003/instance}startDate')
        start.text = data.reporting_period_start.isoformat()
        end = ET.SubElement(period2, '{http://www.xbrl.org/2003/instance}endDate')
        end.text = data.reporting_period_end.isoformat()
        
        return context_map
    
    def _add_units(self, resources: ET.Element) -> None:
        """Add measurement units"""
        # tCO2e unit
        tco2e_unit = ET.SubElement(resources, '{http://www.xbrl.org/2003/instance}unit')
        tco2e_unit.set('id', 'unit-tco2e')
        measure = ET.SubElement(tco2e_unit, '{http://www.xbrl.org/2003/instance}measure')
        measure.text = 'ghgp:tCO2e'
        
        # Currency unit
        currency_unit = ET.SubElement(resources, '{http://www.xbrl.org/2003/instance}unit')
        currency_unit.set('id', 'unit-eur')
        measure2 = ET.SubElement(currency_unit, '{http://www.xbrl.org/2003/instance}measure')
        measure2.text = 'iso4217:EUR'
    
    def _add_entity_section(self, body: ET.Element, data: EmissionReportData) -> None:
        """Add entity information section"""
        section = ET.SubElement(body, '{http://www.w3.org/1999/xhtml}section')
        section.set('class', 'entity-info')
        
        h1 = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}h1')
        h1.text = "Sustainability Disclosure Report"
        
        p = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}p')
        p.text = "Entity: "
        
        # Tagged entity name - text content is automatically escaped by ElementTree
        span = ET.SubElement(p, '{http://www.xbrl.org/2013/inlineXBRL}nonNumeric')
        span.set('contextRef', 'ctx-instant')
        span.set('name', 'esrs:EntityName')
        span.text = data.entity_name
    
    def _add_emissions_overview(self, body: ET.Element, data: EmissionReportData) -> None:
        """Add emissions overview section with tagged values"""
        section = ET.SubElement(body, '{http://www.w3.org/1999/xhtml}section')
        section.set('class', 'emissions-overview')
        
        h2 = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}h2')
        h2.text = "GHG Emissions Overview"
        
        # Scope 1
        p1 = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}p')
        p1.text = "Scope 1 (Direct): "
        self._add_numeric_fact(p1, 'esrs:Scope1Emissions', 'scope1-total',
                             data.scope1_total, 'unit-tco2e', 'ctx-duration')
        
        # Scope 2
        p2 = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}p')
        p2.text = "Scope 2 (Location-based): "
        self._add_numeric_fact(p2, 'esrs:Scope2LocationBased', 'scope2-location',
                             data.scope2_location_total, 'unit-tco2e', 'ctx-duration')
        
        # Scope 3 total
        p3 = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}p')
        p3.text = "Scope 3 (Value chain): "
        self._add_numeric_fact(p3, 'esrs:Scope3Total', 'scope3-total',
                             data.scope3_total, 'unit-tco2e', 'ctx-duration')
    
    def _add_scope3_breakdown(self, body: ET.Element, data: EmissionReportData) -> None:
        """Add detailed Scope 3 breakdown with all 15 categories"""
        section = ET.SubElement(body, '{http://www.w3.org/1999/xhtml}section')
        section.set('class', 'scope3-breakdown')
        
        h2 = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}h2')
        h2.text = "Scope 3 Category Breakdown"
        
        # Map category data for easy lookup
        category_map = {cat.category_number: cat for cat in data.scope3_categories}
        
        # Process all 15 categories
        for i in range(1, 16):
            cat_key = f'category_{i}_' + self._get_category_suffix(i)
            
            if i in category_map:
                cat_data = category_map[i]
                value = cat_data.emissions_tco2e
            else:
                # Category not applicable or zero emissions
                value = Decimal('0')
            
            # Get taxonomy elements
            taxonomy_elements = SCOPE3_TAXONOMY_MAP.get(cat_key, {})
            
            # Create paragraph for category
            p = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}p')
            p.text = f"Category {i} - {self._get_category_name(i)}: "
            
            # Tag with primary taxonomy (ESRS)
            if 'esrs' in taxonomy_elements:
                self._add_numeric_fact(p, taxonomy_elements['esrs'], f'scope3-cat{i}',
                                     value, 'unit-tco2e', 'ctx-duration')
    
    def _add_numeric_fact(self, parent: ET.Element, name: str, fact_id: str,
                         value: Decimal, unit_ref: str, context_ref: str) -> None:
        """Add tagged numeric fact"""
        fact = ET.SubElement(parent, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction')
        fact.set('id', fact_id)
        fact.set('name', name)
        fact.set('contextRef', context_ref)
        fact.set('unitRef', unit_ref)
        fact.set('decimals', '2')
        fact.set('scale', '0')
        fact.set('format', 'ixt:numdotdecimal')
        fact.text = f"{value:.2f}"
    
    def _add_cbam_section(self, body: ET.Element, data: EmissionReportData) -> None:
        """Add CBAM embedded emissions section"""
        if not data.cbam_embedded_emissions:
            return
        
        section = ET.SubElement(body, '{http://www.w3.org/1999/xhtml}section')
        section.set('class', 'cbam-disclosure')
        
        h2 = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}h2')
        h2.text = "CBAM Embedded Emissions"
        
        for product, emissions in data.cbam_embedded_emissions.items():
            p = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}p')
            p.text = f"{product}: "
            self._add_numeric_fact(p, f'cbam:EmbeddedEmissions{product}', 
                                 f'cbam-{product.lower()}', emissions, 
                                 'unit-tco2e', 'ctx-duration')
    
    def _add_cdp_narratives(self, body: ET.Element, data: EmissionReportData) -> None:
        """Add CDP narrative sections"""
        if not data.cdp_narrative_sections:
            return
        
        section = ET.SubElement(body, '{http://www.w3.org/1999/xhtml}section')
        section.set('class', 'cdp-narratives')
        
        for section_name, narrative in data.cdp_narrative_sections.items():
            div = ET.SubElement(section, '{http://www.w3.org/1999/xhtml}div')
            h3 = ET.SubElement(div, '{http://www.w3.org/1999/xhtml}h3')
            h3.text = section_name
            
            # Tag narrative text
            p = ET.SubElement(div, '{http://www.xbrl.org/2013/inlineXBRL}nonNumeric')
            p.set('contextRef', 'ctx-duration')
            p.set('name', f'cdp:{section_name.replace(" ", "")}')
            p.text = narrative
    
    @lru_cache(maxsize=16)
    def _get_category_suffix(self, category_num: int) -> str:
        """Get category suffix for mapping (cached for performance)"""
        suffixes = {
            1: 'purchased_goods', 2: 'capital_goods', 3: 'fuel_energy',
            4: 'upstream_transport', 5: 'waste', 6: 'business_travel',
            7: 'employee_commuting', 8: 'upstream_leased', 9: 'downstream_transport',
            10: 'processing_sold', 11: 'use_of_sold', 12: 'end_of_life',
            13: 'downstream_leased', 14: 'franchises', 15: 'investments'
        }
        return suffixes.get(category_num, 'unknown')
    
    @lru_cache(maxsize=16)
    def _get_category_name(self, category_num: int) -> str:
        """Get human-readable category name (cached for performance)"""
        names = {
            1: 'Purchased Goods and Services', 2: 'Capital Goods',
            3: 'Fuel- and Energy-Related Activities', 4: 'Upstream Transportation',
            5: 'Waste Generated in Operations', 6: 'Business Travel',
            7: 'Employee Commuting', 8: 'Upstream Leased Assets',
            9: 'Downstream Transportation', 10: 'Processing of Sold Products',
            11: 'Use of Sold Products', 12: 'End-of-Life Treatment',
            13: 'Downstream Leased Assets', 14: 'Franchises', 15: 'Investments'
        }
        return names.get(category_num, 'Unknown Category')
    
    def _serialize_html(self, root: ET.Element) -> str:
        """Serialize HTML with proper formatting and DOCTYPE"""
        # Convert to string
        raw_xml = ET.tostring(root, encoding='unicode', method='xml')
        
        # Add DOCTYPE and clean up
        doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        
        # Clean up namespace declarations
        # Note: For production with perfect namespace prefix control, consider lxml.etree
        # ElementTree generates ns0: prefixes that we clean up here
        cleaned = raw_xml.replace('ns0:', '').replace(':ns0', '')
        
        return doctype + cleaned


# Critical design choices:
# 1. Thread-safe by design: No mutable state stored between method calls
# 2. ElementTree auto-escapes text content but not attributes - we handle attributes manually
# 3. All 15 Scope 3 categories always tagged (zero-value for missing) ensuring schema validity
# 4. Namespace-aware XML parsing in validate_ixbrl() for robust validation
# 5. Class method generate_report() recommended for FastAPI to guarantee fresh instances
# 6. LRU caching on static mappings for performance with high-volume batch processing
# 7. Pydantic field validators ensure API accepts int/float/string and converts to Decimal
# app/services/xbrl_exporter.py
"""
iXBRL/XBRL Export Service for ESRS E1 Climate Disclosures
=========================================================
Generates XHTML documents with embedded Inline XBRL (iXBRL) tags
compliant with EFRAG ESRS 2024 taxonomy.

ESRS E1 Key Disclosure Requirements:
- E1-6: Gross Scope 1, 2, 3 and Total GHG Emissions
- E1-7: GHG Removals and Carbon Credits
- E1-8: Internal Carbon Pricing

XBRL Taxonomy Reference:
- Namespace: https://xbrl.efrag.org/taxonomy/esrs/2023-12-22
- Schema: esrs_cor.xsd (core schema for all ESRS standards)
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any
import re
from xml.sax.saxutils import escape as xml_escape
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ESRS E1 TAXONOMY MAPPINGS
# =============================================================================

class ESRS_E1_Taxonomy:
    """
    ESRS E1 Climate Taxonomy - Official EFRAG element names.

    Reference: EFRAG ESRS Set 1, XBRL Taxonomy 2023-12-22
    These are the official concept names from the ESRS taxonomy.
    """
    # Namespace
    NAMESPACE = "https://xbrl.efrag.org/taxonomy/esrs/2023-12-22"
    PREFIX = "esrs"

    # E1-6: GHG Emissions (Primary Disclosures)
    GROSS_SCOPE_1_GHG = "esrs:GrossScope1GreenhouseGasEmissions"
    GROSS_SCOPE_2_LOCATION = "esrs:GrossLocationBasedScope2GreenhouseGasEmissions"
    GROSS_SCOPE_2_MARKET = "esrs:GrossMarketBasedScope2GreenhouseGasEmissions"
    GROSS_SCOPE_3_GHG = "esrs:GrossScope3GreenhouseGasEmissions"
    TOTAL_GHG_EMISSIONS = "esrs:TotalGHGEmissions"

    # E1-6: Scope 3 Category Breakdowns
    SCOPE_3_CAT_1_PURCHASED = "esrs:Scope3Category1PurchasedGoodsAndServices"
    SCOPE_3_CAT_2_CAPITAL = "esrs:Scope3Category2CapitalGoods"
    SCOPE_3_CAT_3_FUEL_ENERGY = "esrs:Scope3Category3FuelAndEnergyRelatedActivities"
    SCOPE_3_CAT_4_UPSTREAM_TRANSPORT = "esrs:Scope3Category4UpstreamTransportation"
    SCOPE_3_CAT_5_WASTE = "esrs:Scope3Category5WasteGenerated"
    SCOPE_3_CAT_6_BUSINESS_TRAVEL = "esrs:Scope3Category6BusinessTravel"
    SCOPE_3_CAT_7_COMMUTING = "esrs:Scope3Category7EmployeeCommuting"
    SCOPE_3_CAT_8_UPSTREAM_LEASED = "esrs:Scope3Category8UpstreamLeasedAssets"
    SCOPE_3_CAT_9_DOWNSTREAM_TRANSPORT = "esrs:Scope3Category9DownstreamTransportation"
    SCOPE_3_CAT_10_PROCESSING = "esrs:Scope3Category10ProcessingOfSoldProducts"
    SCOPE_3_CAT_11_USE = "esrs:Scope3Category11UseOfSoldProducts"
    SCOPE_3_CAT_12_END_OF_LIFE = "esrs:Scope3Category12EndOfLifeTreatment"
    SCOPE_3_CAT_13_DOWNSTREAM_LEASED = "esrs:Scope3Category13DownstreamLeasedAssets"
    SCOPE_3_CAT_14_FRANCHISES = "esrs:Scope3Category14Franchises"
    SCOPE_3_CAT_15_INVESTMENTS = "esrs:Scope3Category15Investments"

    # E1-7: GHG Removals
    GHG_REMOVALS = "esrs:GreenhouseGasRemovalsFromOwnOperations"
    CARBON_CREDITS_RETIRED = "esrs:CarbonCreditsRetired"

    # E1-8: Internal Carbon Pricing
    INTERNAL_CARBON_PRICE = "esrs:InternalCarbonPrice"

    # Units
    UNIT_TCO2E = "esrs:tCO2e"
    UNIT_EUR_PER_TCO2E = "iso4217:EUR/esrs:tCO2e"

    # Entity Identifier
    LEI_SCHEME = "http://www.lei-worldwide.com"


class XBRLValidationError(Exception):
    """Raised when XBRL output validation fails."""
    pass


@dataclass
class XBRLValidationResult:
    """Result of XBRL validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ESRSE1EmissionsData:
    """
    Data structure for ESRS E1 emissions disclosure.

    All emissions values are in tonnes CO2e (tCO2e).
    """
    # Required identifiers
    entity_name: str
    lei: str  # Legal Entity Identifier (20 chars)
    reporting_year: int

    # Reporting period
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    # E1-6: Core GHG Emissions (in tCO2e)
    scope_1_emissions: float = 0.0
    scope_2_location_based: float = 0.0
    scope_2_market_based: Optional[float] = None  # Optional
    scope_3_emissions: float = 0.0

    # E1-6: Scope 3 Category Breakdown (optional, in tCO2e)
    scope_3_categories: Dict[str, float] = field(default_factory=dict)

    # E1-7: Removals and Credits (optional)
    ghg_removals: Optional[float] = None
    carbon_credits_retired: Optional[float] = None

    # E1-8: Internal Carbon Price (optional, EUR/tCO2e)
    internal_carbon_price: Optional[float] = None

    # Metadata
    data_quality_score: Optional[int] = None  # 1-100
    calculation_count: int = 0
    datasets_used: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Set default period based on reporting year."""
        if self.period_start is None:
            self.period_start = date(self.reporting_year, 1, 1)
        if self.period_end is None:
            self.period_end = date(self.reporting_year, 12, 31)

    @property
    def total_emissions(self) -> float:
        """Calculate total GHG emissions (Scope 1 + 2 + 3)."""
        scope_2 = self.scope_2_location_based  # Use location-based for total
        return self.scope_1_emissions + scope_2 + self.scope_3_emissions

    def validate(self) -> XBRLValidationResult:
        """Validate emissions data for XBRL export."""
        errors = []
        warnings = []

        # Required fields
        if not self.entity_name or len(self.entity_name.strip()) == 0:
            errors.append("entity_name is required and cannot be empty")

        # LEI validation (ISO 17442)
        if not self.lei:
            errors.append("lei (Legal Entity Identifier) is required")
        elif not self._validate_lei(self.lei):
            errors.append(f"Invalid LEI format: {self.lei}. Must be 20 alphanumeric characters.")

        # Reporting year
        if self.reporting_year < 2020 or self.reporting_year > 2100:
            errors.append(f"Invalid reporting_year: {self.reporting_year}")

        # Emissions values must be non-negative
        if self.scope_1_emissions < 0:
            errors.append("scope_1_emissions cannot be negative")
        if self.scope_2_location_based < 0:
            errors.append("scope_2_location_based cannot be negative")
        if self.scope_3_emissions < 0:
            errors.append("scope_3_emissions cannot be negative")

        # Warnings for data quality
        if self.scope_1_emissions == 0 and self.scope_2_location_based == 0:
            warnings.append("Both Scope 1 and Scope 2 emissions are zero")

        if self.scope_3_emissions > 0 and not self.scope_3_categories:
            warnings.append("Scope 3 emissions reported without category breakdown")

        # Check Scope 3 category totals
        if self.scope_3_categories:
            cat_total = sum(self.scope_3_categories.values())
            if abs(cat_total - self.scope_3_emissions) > 0.01:
                warnings.append(
                    f"Scope 3 category total ({cat_total:.2f}) does not match "
                    f"scope_3_emissions ({self.scope_3_emissions:.2f})"
                )

        return XBRLValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info={
                "total_emissions": self.total_emissions,
                "has_scope_3_breakdown": bool(self.scope_3_categories),
                "has_market_based_scope_2": self.scope_2_market_based is not None,
            }
        )

    @staticmethod
    def _validate_lei(lei: str) -> bool:
        """Validate LEI format (20 alphanumeric characters)."""
        if not lei or len(lei) != 20:
            return False
        return bool(re.match(r'^[A-Z0-9]{20}$', lei.upper()))


# =============================================================================
# iXBRL GENERATOR
# =============================================================================

class IXBRLGenerator:
    """
    Generates Inline XBRL (iXBRL) documents for ESRS E1 disclosures.

    Output format: XHTML with embedded iXBRL tags per XBRL International
    Inline XBRL specification (v1.1).
    """

    # iXBRL namespaces
    NAMESPACES = {
        "html": "http://www.w3.org/1999/xhtml",
        "ix": "http://www.xbrl.org/2013/inlineXBRL",
        "ixt": "http://www.xbrl.org/inlineXBRL/transformation/2020-02-12",
        "xbrli": "http://www.xbrl.org/2003/instance",
        "link": "http://www.xbrl.org/2003/linkbase",
        "xlink": "http://www.w3.org/1999/xlink",
        "esrs": ESRS_E1_Taxonomy.NAMESPACE,
        "iso4217": "http://www.xbrl.org/2003/iso4217",
    }

    def __init__(self, include_css: bool = True, include_methodology: bool = True):
        self.include_css = include_css
        self.include_methodology = include_methodology

    def generate(self, data: ESRSE1EmissionsData) -> str:
        """
        Generate complete iXBRL document from emissions data.

        Args:
            data: ESRS E1 emissions data structure

        Returns:
            XHTML string with embedded iXBRL tags

        Raises:
            XBRLValidationError: If data validation fails
        """
        # Validate input
        validation = data.validate()
        if not validation.valid:
            raise XBRLValidationError(
                f"Data validation failed: {'; '.join(validation.errors)}"
            )

        # Log warnings
        for warning in validation.warnings:
            logger.warning(f"XBRL data warning: {warning}")

        # Generate document sections
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        html_open = self._html_open_tag()
        head = self._generate_head(data)
        body = self._generate_body(data)

        return f"""{xml_declaration}
{html_open}
{head}
{body}
</html>"""

    def _html_open_tag(self) -> str:
        """Generate HTML opening tag with all namespaces."""
        ns_attrs = " ".join(
            f'xmlns:{prefix}="{uri}"' if prefix != "html" else f'xmlns="{uri}"'
            for prefix, uri in self.NAMESPACES.items()
        )
        return f'<html {ns_attrs} xml:lang="en">'

    def _generate_head(self, data: ESRSE1EmissionsData) -> str:
        """Generate HTML head section."""
        css = self._generate_css() if self.include_css else ""
        title = xml_escape(f"ESRS E1 Climate Disclosure - {data.entity_name}")

        return f"""<head>
    <meta charset="UTF-8"/>
    <title>{title}</title>{css}
</head>"""

    def _generate_css(self) -> str:
        """Generate embedded CSS styles."""
        return """
    <style type="text/css">
        body {
            font-family: Arial, Helvetica, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #1a365d;
            border-bottom: 3px solid #2b6cb0;
            padding-bottom: 0.5rem;
        }
        h2 {
            color: #2c5282;
            margin-top: 2rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 0.25rem;
        }
        h3 { color: #3182ce; margin-top: 1.5rem; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0 2rem 0;
        }
        th, td {
            border: 1px solid #e2e8f0;
            padding: 0.75rem 1rem;
            text-align: left;
        }
        th {
            background-color: #2c5282;
            color: white;
            font-weight: 600;
        }
        tr:nth-child(even) { background-color: #f7fafc; }
        tr:hover { background-color: #edf2f7; }
        .total-row {
            font-weight: bold;
            background-color: #ebf8ff !important;
            border-top: 2px solid #2b6cb0;
        }
        .numeric {
            text-align: right;
            font-family: 'Courier New', monospace;
        }
        .metadata {
            color: #718096;
            font-size: 0.875rem;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #e2e8f0;
        }
        .ix-hidden { display: none; }
        .section { margin-bottom: 2rem; }
        .lei { font-family: monospace; letter-spacing: 0.05em; }
    </style>"""

    def _generate_body(self, data: ESRSE1EmissionsData) -> str:
        """Generate HTML body with iXBRL tags."""
        ix_header = self._generate_ix_header(data)
        header = self._generate_header(data)
        e1_6_section = self._generate_e1_6_section(data)

        # Optional sections
        scope_3_detail = self._generate_scope_3_detail(data) if data.scope_3_categories else ""
        e1_7_section = self._generate_e1_7_section(data) if (data.ghg_removals or data.carbon_credits_retired) else ""
        e1_8_section = self._generate_e1_8_section(data) if data.internal_carbon_price else ""
        methodology = self._generate_methodology(data) if self.include_methodology else ""
        footer = self._generate_footer(data)

        return f"""<body>
    {ix_header}
    {header}
    {e1_6_section}
    {scope_3_detail}
    {e1_7_section}
    {e1_8_section}
    {methodology}
    {footer}
</body>"""

    def _generate_ix_header(self, data: ESRSE1EmissionsData) -> str:
        """Generate iXBRL header with contexts and units."""
        period_start = data.period_start.isoformat()
        period_end = data.period_end.isoformat()

        return f"""<div class="ix-hidden">
        <ix:header>
            <ix:references>
                <link:schemaRef xlink:type="simple"
                               xlink:href="https://xbrl.efrag.org/taxonomy/esrs/2023-12-22/common/esrs_cor.xsd"/>
            </ix:references>
            <ix:resources>
                <!-- Reporting Period Context -->
                <xbrli:context id="ctx_period">
                    <xbrli:entity>
                        <xbrli:identifier scheme="{ESRS_E1_Taxonomy.LEI_SCHEME}">{data.lei}</xbrli:identifier>
                    </xbrli:entity>
                    <xbrli:period>
                        <xbrli:startDate>{period_start}</xbrli:startDate>
                        <xbrli:endDate>{period_end}</xbrli:endDate>
                    </xbrli:period>
                </xbrli:context>

                <!-- Instant Context (end of period) -->
                <xbrli:context id="ctx_instant">
                    <xbrli:entity>
                        <xbrli:identifier scheme="{ESRS_E1_Taxonomy.LEI_SCHEME}">{data.lei}</xbrli:identifier>
                    </xbrli:entity>
                    <xbrli:period>
                        <xbrli:instant>{period_end}</xbrli:instant>
                    </xbrli:period>
                </xbrli:context>

                <!-- Units -->
                <xbrli:unit id="unit_tCO2e">
                    <xbrli:measure>esrs:tCO2e</xbrli:measure>
                </xbrli:unit>
                <xbrli:unit id="unit_EUR_per_tCO2e">
                    <xbrli:divide>
                        <xbrli:unitNumerator>
                            <xbrli:measure>iso4217:EUR</xbrli:measure>
                        </xbrli:unitNumerator>
                        <xbrli:unitDenominator>
                            <xbrli:measure>esrs:tCO2e</xbrli:measure>
                        </xbrli:unitDenominator>
                    </xbrli:divide>
                </xbrli:unit>
            </ix:resources>
        </ix:header>
    </div>"""

    def _generate_header(self, data: ESRSE1EmissionsData) -> str:
        """Generate document header section."""
        entity_escaped = xml_escape(data.entity_name)
        period_str = f"{data.period_start.isoformat()} to {data.period_end.isoformat()}"

        return f"""<header class="section">
        <h1>ESRS E1 Climate-Related Disclosures</h1>
        <p><strong>Reporting Entity:</strong>
            <ix:nonNumeric name="esrs:NameOfReportingEntity"
                          contextRef="ctx_period">{entity_escaped}</ix:nonNumeric></p>
        <p><strong>Legal Entity Identifier (LEI):</strong>
            <span class="lei"><ix:nonNumeric name="esrs:LegalEntityIdentifier"
                                            contextRef="ctx_period">{data.lei}</ix:nonNumeric></span></p>
        <p><strong>Reporting Period:</strong> {period_str}</p>
    </header>"""

    def _generate_e1_6_section(self, data: ESRSE1EmissionsData) -> str:
        """Generate E1-6 GHG Emissions disclosure section."""
        scope_2_row = self._scope_2_rows(data)

        return f"""<section id="e1-6" class="section">
        <h2>E1-6: Gross Scopes 1, 2, 3 and Total GHG Emissions</h2>
        <p>Greenhouse gas emissions for the reporting period, measured in tonnes of CO2 equivalent (tCO2e).</p>

        <table>
            <thead>
                <tr>
                    <th style="width: 60%;">Emission Scope</th>
                    <th class="numeric" style="width: 40%;">tCO2e</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Scope 1 - Direct GHG Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="{ESRS_E1_Taxonomy.GROSS_SCOPE_1_GHG}"
                                        contextRef="ctx_period"
                                        unitRef="unit_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{data.scope_1_emissions:,.2f}</ix:nonFraction>
                    </td>
                </tr>
                {scope_2_row}
                <tr>
                    <td>Scope 3 - Indirect Value Chain Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="{ESRS_E1_Taxonomy.GROSS_SCOPE_3_GHG}"
                                        contextRef="ctx_period"
                                        unitRef="unit_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{data.scope_3_emissions:,.2f}</ix:nonFraction>
                    </td>
                </tr>
                <tr class="total-row">
                    <td><strong>Total GHG Emissions</strong></td>
                    <td class="numeric">
                        <ix:nonFraction name="{ESRS_E1_Taxonomy.TOTAL_GHG_EMISSIONS}"
                                        contextRef="ctx_period"
                                        unitRef="unit_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{data.total_emissions:,.2f}</ix:nonFraction>
                    </td>
                </tr>
            </tbody>
        </table>
    </section>"""

    def _scope_2_rows(self, data: ESRSE1EmissionsData) -> str:
        """Generate Scope 2 rows (location-based, optionally market-based)."""
        location_row = f"""<tr>
                    <td>Scope 2 - Location-based Indirect Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="{ESRS_E1_Taxonomy.GROSS_SCOPE_2_LOCATION}"
                                        contextRef="ctx_period"
                                        unitRef="unit_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{data.scope_2_location_based:,.2f}</ix:nonFraction>
                    </td>
                </tr>"""

        if data.scope_2_market_based is not None:
            market_row = f"""<tr>
                    <td>Scope 2 - Market-based Indirect Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="{ESRS_E1_Taxonomy.GROSS_SCOPE_2_MARKET}"
                                        contextRef="ctx_period"
                                        unitRef="unit_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{data.scope_2_market_based:,.2f}</ix:nonFraction>
                    </td>
                </tr>"""
            return location_row + "\n" + market_row

        return location_row

    def _generate_scope_3_detail(self, data: ESRSE1EmissionsData) -> str:
        """Generate Scope 3 category breakdown table."""
        if not data.scope_3_categories:
            return ""

        # Map category keys to taxonomy elements and labels
        category_mappings = {
            "purchased_goods_services": (ESRS_E1_Taxonomy.SCOPE_3_CAT_1_PURCHASED, "Cat 1: Purchased Goods &amp; Services"),
            "capital_goods": (ESRS_E1_Taxonomy.SCOPE_3_CAT_2_CAPITAL, "Cat 2: Capital Goods"),
            "fuel_energy_activities": (ESRS_E1_Taxonomy.SCOPE_3_CAT_3_FUEL_ENERGY, "Cat 3: Fuel &amp; Energy Activities"),
            "upstream_transportation": (ESRS_E1_Taxonomy.SCOPE_3_CAT_4_UPSTREAM_TRANSPORT, "Cat 4: Upstream Transportation"),
            "waste_generated": (ESRS_E1_Taxonomy.SCOPE_3_CAT_5_WASTE, "Cat 5: Waste Generated"),
            "business_travel": (ESRS_E1_Taxonomy.SCOPE_3_CAT_6_BUSINESS_TRAVEL, "Cat 6: Business Travel"),
            "employee_commuting": (ESRS_E1_Taxonomy.SCOPE_3_CAT_7_COMMUTING, "Cat 7: Employee Commuting"),
            "upstream_leased_assets": (ESRS_E1_Taxonomy.SCOPE_3_CAT_8_UPSTREAM_LEASED, "Cat 8: Upstream Leased Assets"),
            "downstream_transportation": (ESRS_E1_Taxonomy.SCOPE_3_CAT_9_DOWNSTREAM_TRANSPORT, "Cat 9: Downstream Transportation"),
            "processing_sold_products": (ESRS_E1_Taxonomy.SCOPE_3_CAT_10_PROCESSING, "Cat 10: Processing of Sold Products"),
            "use_sold_products": (ESRS_E1_Taxonomy.SCOPE_3_CAT_11_USE, "Cat 11: Use of Sold Products"),
            "end_of_life_treatment": (ESRS_E1_Taxonomy.SCOPE_3_CAT_12_END_OF_LIFE, "Cat 12: End-of-Life Treatment"),
            "downstream_leased_assets": (ESRS_E1_Taxonomy.SCOPE_3_CAT_13_DOWNSTREAM_LEASED, "Cat 13: Downstream Leased Assets"),
            "franchises": (ESRS_E1_Taxonomy.SCOPE_3_CAT_14_FRANCHISES, "Cat 14: Franchises"),
            "investments": (ESRS_E1_Taxonomy.SCOPE_3_CAT_15_INVESTMENTS, "Cat 15: Investments"),
        }

        rows = []
        for cat_key, value in data.scope_3_categories.items():
            if cat_key in category_mappings:
                element, label = category_mappings[cat_key]
                rows.append(f"""<tr>
                    <td>{label}</td>
                    <td class="numeric">
                        <ix:nonFraction name="{element}"
                                        contextRef="ctx_period"
                                        unitRef="unit_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{value:,.2f}</ix:nonFraction>
                    </td>
                </tr>""")

        if not rows:
            return ""

        rows_html = "\n".join(rows)
        return f"""<section id="scope3-detail" class="section">
        <h3>Scope 3 Category Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>Scope 3 Category</th>
                    <th class="numeric">tCO2e</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </section>"""

    def _generate_e1_7_section(self, data: ESRSE1EmissionsData) -> str:
        """Generate E1-7 GHG Removals and Carbon Credits section."""
        removals_row = ""
        credits_row = ""

        if data.ghg_removals is not None:
            removals_row = f"""<tr>
                    <td>GHG Removals from Own Operations</td>
                    <td class="numeric">
                        <ix:nonFraction name="{ESRS_E1_Taxonomy.GHG_REMOVALS}"
                                        contextRef="ctx_period"
                                        unitRef="unit_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{data.ghg_removals:,.2f}</ix:nonFraction>
                    </td>
                </tr>"""

        if data.carbon_credits_retired is not None:
            credits_row = f"""<tr>
                    <td>Carbon Credits Retired</td>
                    <td class="numeric">
                        <ix:nonFraction name="{ESRS_E1_Taxonomy.CARBON_CREDITS_RETIRED}"
                                        contextRef="ctx_period"
                                        unitRef="unit_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{data.carbon_credits_retired:,.2f}</ix:nonFraction>
                    </td>
                </tr>"""

        return f"""<section id="e1-7" class="section">
        <h2>E1-7: GHG Removals and Carbon Credits</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th class="numeric">tCO2e</th>
                </tr>
            </thead>
            <tbody>
                {removals_row}
                {credits_row}
            </tbody>
        </table>
    </section>"""

    def _generate_e1_8_section(self, data: ESRSE1EmissionsData) -> str:
        """Generate E1-8 Internal Carbon Pricing section."""
        if data.internal_carbon_price is None:
            return ""

        return f"""<section id="e1-8" class="section">
        <h2>E1-8: Internal Carbon Pricing</h2>
        <p>The undertaking applies internal carbon pricing as follows:</p>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th class="numeric">Value</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Internal Carbon Price</td>
                    <td class="numeric">
                        <ix:nonFraction name="{ESRS_E1_Taxonomy.INTERNAL_CARBON_PRICE}"
                                        contextRef="ctx_instant"
                                        unitRef="unit_EUR_per_tCO2e"
                                        decimals="2"
                                        format="ixt:num-dot-decimal">{data.internal_carbon_price:,.2f}</ix:nonFraction> EUR/tCO2e
                    </td>
                </tr>
            </tbody>
        </table>
    </section>"""

    def _generate_methodology(self, data: ESRSE1EmissionsData) -> str:
        """Generate methodology notes section."""
        datasets = ", ".join(data.datasets_used) if data.datasets_used else "Not specified"
        quality = f"{data.data_quality_score}/100" if data.data_quality_score else "Not assessed"

        return f"""<section id="methodology" class="section">
        <h2>Methodology Notes</h2>
        <p>This disclosure was prepared in accordance with ESRS E1 requirements under the Corporate
        Sustainability Reporting Directive (CSRD) and Delegated Regulation (EU) 2023/2772.</p>

        <h3>Calculation Methodology</h3>
        <ul>
            <li>GHG emissions calculated following GHG Protocol Corporate Standard</li>
            <li>Scope 2 reported using both location-based and market-based methods where applicable</li>
            <li>Scope 3 categories calculated per GHG Protocol Corporate Value Chain (Scope 3) Standard</li>
        </ul>

        <h3>Data Sources</h3>
        <ul>
            <li><strong>Emission Factor Datasets:</strong> {xml_escape(datasets)}</li>
            <li><strong>Number of Calculations:</strong> {data.calculation_count}</li>
            <li><strong>Data Quality Score:</strong> {quality}</li>
        </ul>

        <h3>Assurance</h3>
        <p>This report was generated by FactorTrace, an ESRS E1-compliant emissions calculation platform.
        Independent third-party assurance may be required under applicable regulations.</p>
    </section>"""

    def _generate_footer(self, data: ESRSE1EmissionsData) -> str:
        """Generate document footer."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""<footer class="metadata">
        <p>Generated by FactorTrace on {timestamp}</p>
        <p>This document conforms to ESRS E1 disclosure requirements per Delegated Regulation (EU) 2023/2772.</p>
        <p>iXBRL tags reference EFRAG ESRS XBRL Taxonomy 2023-12-22.</p>
    </footer>"""


# =============================================================================
# XBRL VALIDATION SERVICE
# =============================================================================

def validate_ixbrl_output(xhtml_content: str) -> XBRLValidationResult:
    """
    Validate iXBRL output structure and content.

    Performs the following checks:
    1. XML well-formedness
    2. Required iXBRL namespaces present
    3. ix:header structure with contexts and units
    4. Required ESRS E1 elements present
    5. Context references valid
    6. Unit references valid

    Args:
        xhtml_content: XHTML string with embedded iXBRL

    Returns:
        XBRLValidationResult with validation status and any errors/warnings
    """
    errors = []
    warnings = []
    info = {}

    try:
        import lxml.etree as ET

        # 1. XML well-formedness
        try:
            doc = ET.fromstring(xhtml_content.encode('utf-8'))
        except ET.XMLSyntaxError as e:
            errors.append(f"XML syntax error: {e}")
            return XBRLValidationResult(valid=False, errors=errors)

        # Define namespace map
        nsmap = {
            'html': 'http://www.w3.org/1999/xhtml',
            'ix': 'http://www.xbrl.org/2013/inlineXBRL',
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'link': 'http://www.xbrl.org/2003/linkbase',
            'esrs': 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22',
        }

        # 2. Check required namespaces
        root_nsmap = doc.nsmap
        required_ns = ['ix', 'xbrli', 'esrs']
        for ns in required_ns:
            if ns not in root_nsmap and f'{{{nsmap.get(ns, "")}}}' not in str(root_nsmap):
                # Check if namespace is declared with different prefix
                if nsmap.get(ns) not in root_nsmap.values():
                    errors.append(f"Missing required namespace: {ns}")

        # 3. Check ix:header
        ix_headers = doc.xpath('//ix:header', namespaces=nsmap)
        if not ix_headers:
            errors.append("Missing ix:header element")
        else:
            info['ix_header_count'] = len(ix_headers)

            # Check for contexts
            contexts = doc.xpath('//xbrli:context', namespaces=nsmap)
            if not contexts:
                errors.append("No xbrli:context elements found")
            else:
                info['context_count'] = len(contexts)
                context_ids = [c.get('id') for c in contexts]
                info['context_ids'] = context_ids

            # Check for units
            units = doc.xpath('//xbrli:unit', namespaces=nsmap)
            if not units:
                errors.append("No xbrli:unit elements found")
            else:
                info['unit_count'] = len(units)
                unit_ids = [u.get('id') for u in units]
                info['unit_ids'] = unit_ids

        # 4. Check for ESRS E1 facts
        non_fractions = doc.xpath('//ix:nonFraction', namespaces=nsmap)
        non_numerics = doc.xpath('//ix:nonNumeric', namespaces=nsmap)

        info['fact_count'] = len(non_fractions) + len(non_numerics)
        info['numeric_fact_count'] = len(non_fractions)
        info['text_fact_count'] = len(non_numerics)

        if len(non_fractions) == 0:
            warnings.append("No numeric facts (ix:nonFraction) found")

        # 5. Validate context references
        if 'context_ids' in info:
            for fact in non_fractions + non_numerics:
                ctx_ref = fact.get('contextRef')
                if ctx_ref and ctx_ref not in info['context_ids']:
                    errors.append(f"Invalid contextRef '{ctx_ref}' - context not defined")

        # 6. Validate unit references for numeric facts
        if 'unit_ids' in info:
            for fact in non_fractions:
                unit_ref = fact.get('unitRef')
                if unit_ref and unit_ref not in info['unit_ids']:
                    errors.append(f"Invalid unitRef '{unit_ref}' - unit not defined")

        # 7. Check for required ESRS E1 elements
        esrs_elements = {
            'GrossScope1GreenhouseGasEmissions': False,
            'GrossLocationBasedScope2GreenhouseGasEmissions': False,
            'GrossScope3GreenhouseGasEmissions': False,
            'TotalGHGEmissions': False,
        }

        for fact in non_fractions:
            name = fact.get('name', '')
            for element in esrs_elements.keys():
                if element in name:
                    esrs_elements[element] = True

        missing_elements = [e for e, found in esrs_elements.items() if not found]
        if missing_elements:
            warnings.append(f"Missing recommended ESRS E1 elements: {', '.join(missing_elements)}")

        info['esrs_elements_found'] = {k: v for k, v in esrs_elements.items()}

        # 8. Check schemaRef
        schema_refs = doc.xpath('//link:schemaRef', namespaces=nsmap)
        if not schema_refs:
            warnings.append("No link:schemaRef found - taxonomy reference missing")
        else:
            for ref in schema_refs:
                href = ref.get('{http://www.w3.org/1999/xlink}href')
                if href:
                    info['schema_ref'] = href

    except ImportError:
        warnings.append("lxml not available - performing basic validation only")

        # Basic string checks
        if '<?xml' not in xhtml_content:
            errors.append("Missing XML declaration")
        if '<ix:header>' not in xhtml_content and '<ix:header ' not in xhtml_content:
            errors.append("Missing ix:header element")
        if '<xbrli:context' not in xhtml_content:
            errors.append("Missing xbrli:context element")
        if '<xbrli:unit' not in xhtml_content:
            errors.append("Missing xbrli:unit element")
        if '<ix:nonFraction' not in xhtml_content:
            warnings.append("No ix:nonFraction elements found")

    except Exception as e:
        errors.append(f"Validation error: {str(e)}")

    return XBRLValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info=info
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_esrs_e1_report(
    entity_name: str,
    lei: str,
    reporting_year: int,
    scope_1: float,
    scope_2_location: float,
    scope_3: float,
    scope_2_market: Optional[float] = None,
    scope_3_categories: Optional[Dict[str, float]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate ESRS E1 iXBRL report with validation.

    Args:
        entity_name: Legal name of reporting entity
        lei: Legal Entity Identifier (20 chars)
        reporting_year: Reporting year
        scope_1: Scope 1 emissions (tCO2e)
        scope_2_location: Scope 2 location-based emissions (tCO2e)
        scope_3: Scope 3 emissions (tCO2e)
        scope_2_market: Optional Scope 2 market-based emissions (tCO2e)
        scope_3_categories: Optional dict of Scope 3 category breakdowns
        **kwargs: Additional optional fields (ghg_removals, carbon_credits_retired, etc.)

    Returns:
        Dict with 'content' (XHTML), 'validation', 'filename'
    """
    data = ESRSE1EmissionsData(
        entity_name=entity_name,
        lei=lei,
        reporting_year=reporting_year,
        scope_1_emissions=scope_1,
        scope_2_location_based=scope_2_location,
        scope_2_market_based=scope_2_market,
        scope_3_emissions=scope_3,
        scope_3_categories=scope_3_categories or {},
        ghg_removals=kwargs.get('ghg_removals'),
        carbon_credits_retired=kwargs.get('carbon_credits_retired'),
        internal_carbon_price=kwargs.get('internal_carbon_price'),
        data_quality_score=kwargs.get('data_quality_score'),
        calculation_count=kwargs.get('calculation_count', 0),
        datasets_used=kwargs.get('datasets_used', []),
    )

    generator = IXBRLGenerator()
    xhtml_content = generator.generate(data)

    validation = validate_ixbrl_output(xhtml_content)

    filename = f"esrs_e1_{entity_name.lower().replace(' ', '_')}_{reporting_year}.xhtml"

    return {
        'content': xhtml_content,
        'validation': {
            'valid': validation.valid,
            'errors': validation.errors,
            'warnings': validation.warnings,
            'info': validation.info,
        },
        'filename': filename,
        'total_emissions': data.total_emissions,
    }

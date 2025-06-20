from __future__ import annotations
#!/usr/bin/env python3
"""
Batch XHTML/iXBRL Report Generator for CSRD/ESRS Compliance
Production-grade automation for processing supplier emissions data at scale
Enhanced with AI-powered data quality analysis
"""

import csv
import json
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import re

# Assume these are imported from existing modules
from xhtml_generator import generate_ixbrl
from arelle_validator import validate_with_arelle


# Configure logging for production environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
logger = logging.getLogger(__name__)


@dataclass
class DataQualityFeedback:
    """AI-generated data quality feedback"""
    severity: str  # 'critical', 'warning', 'suggestion'
    field: str
    issue: str
    recommendation: str
    compliance_impact: str
    
    def to_string(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.issue} | Recommendation: {self.recommendation}"


@dataclass
class ProcessingResult:
    """Result of processing a single company's report"""
    lei: str
    input_row_number: int
    output_path: str
    validation_status: str  # 'success', 'failed', 'error'
    validation_errors: List[str] = field(default_factory=list)
    data_quality_feedback: List[DataQualityFeedback] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_csv_row(self) -> Dict[str, Any]:
        """Convert to flat dictionary for CSV output"""
        return {
            'lei': self.lei,
            'row_number': self.input_row_number,
            'output_file': self.output_path,
            'validation_status': self.validation_status,
            'errors': ' | '.join(self.validation_errors) if self.validation_errors else '',
            'data_quality_issues': ' | '.join(f.to_string() for f in self.data_quality_feedback) if self.data_quality_feedback else '',
            'critical_issues_count': sum(1 for f in self.data_quality_feedback if f.severity == 'critical'),
            'warning_count': sum(1 for f in self.data_quality_feedback if f.severity == 'warning'),
            'processing_time': self.processing_time_seconds,
            'timestamp': self.timestamp
        }


class AIDataQualityAnalyzer:
    """
    AI-powered data quality analyzer for CSRD/ESRS compliance
    This is a mock implementation that would be replaced with GPT/Claude API in production
    """
    
    def __init__(self):
        # Industry benchmarks and thresholds
        self.benchmarks = {
            'scope3_to_total_ratio': {'min': 0.4, 'max': 0.95},  # Scope 3 typically 40-95% of total
            'scope1_to_scope2_ratio': {'min': 0.1, 'max': 10.0},  # Reasonable range
            'water_efficiency': {'min': 0.7, 'max': 0.95},  # Consumption/withdrawal ratio
            'recycling_rate': {'min': 0.2, 'max': 0.95},  # Industry typical rates
        }
        
        # CSRD mandatory disclosure requirements
        self.mandatory_fields = {
            'scope1_emissions', 'scope2_emissions_location', 'total_emissions'
        }
    
    def analyze_emissions_data(self, data: Dict[str, Any]) -> List[DataQualityFeedback]:
        """Analyze emissions data quality and compliance"""
        feedback = []
        
        try:
            # Convert to floats for analysis
            total = float(data.get('total_emissions', 0))
            scope1 = float(data.get('scope1_emissions', 0))
            scope2_location = float(data.get('scope2_emissions_location', 0))
            scope2_market = float(data.get('scope2_emissions_market', 0))
            scope3 = float(data.get('scope3_emissions', 0))
            
            # Check for missing mandatory data
            if total == 0:
                feedback.append(DataQualityFeedback(
                    severity='critical',
                    field='total_emissions',
                    issue='Total GHG emissions is zero or missing',
                    recommendation='Calculate total emissions as sum of Scope 1, 2, and 3. This is mandatory under ESRS E1-6.',
                    compliance_impact='Non-compliant with ESRS E1 mandatory disclosure requirements'
            
            # Check scope consistency
            calculated_total = scope1 + scope2_location + scope3
            if abs(total - calculated_total) > 0.01:
                feedback.append(DataQualityFeedback(
                    severity='warning',
                    field='total_emissions',
                    issue=f'Total emissions ({total}) does not match sum of scopes ({calculated_total:.1f})',
                    recommendation='Verify calculation methodology. Total should equal Scope 1 + Scope 2 (location-based) + Scope 3.',
                    compliance_impact='May trigger auditor questions during limited assurance'
            
            # Check Scope 3 presence and magnitude
            if scope3 == 0 and total > 0:
                feedback.append(DataQualityFeedback(
                    severity='critical',
                    field='scope3_emissions',
                    issue='Scope 3 emissions reported as zero',
                    recommendation='Scope 3 is mandatory under CSRD. Consider: (1) Supplier-specific data collection, (2) Spend-based estimation using EEIO factors, (3) Average-data method for key categories. Start with Categories 1 (Purchased goods) and 11 (Use of sold products).',
                    compliance_impact='Non-compliant with ESRS E1-9 requiring Scope 3 disclosure'
            elif total > 0:
                scope3_ratio = scope3 / total if total > 0 else 0
                if scope3_ratio < self.benchmarks['scope3_to_total_ratio']['min']:
                    feedback.append(DataQualityFeedback(
                        severity='warning',
                        field='scope3_emissions',
                        issue=f'Scope 3 represents only {scope3_ratio*100:.1f}% of total emissions',
                        recommendation='Scope 3 typically represents 70-90% of total emissions. Review calculation methodology, especially Categories 1, 3, 4, and 11. Consider using GHG Protocol Scope 3 Evaluator tool.',
                        compliance_impact='May indicate incomplete Scope 3 assessment'
            
            # Check market-based vs location-based
            if scope2_market > scope2_location * 1.5:
                feedback.append(DataQualityFeedback(
                    severity='warning',
                    field='scope2_emissions_market',
                    issue='Market-based emissions significantly higher than location-based',
                    recommendation='Verify renewable energy certificates (RECs) and power purchase agreements (PPAs). Market-based should typically be lower than location-based if using renewable energy.',
                    compliance_impact='May indicate data quality issues'
            
            # Check for suspiciously round numbers
            if total > 1000 and total % 1000 == 0:
                feedback.append(DataQualityFeedback(
                    severity='suggestion',
                    field='total_emissions',
                    issue='Emissions value appears to be rounded to nearest thousand',
                    recommendation='Consider reporting with appropriate precision (1-2 decimal places) to demonstrate calculation rigor.',
                    compliance_impact='May raise questions about data quality during assurance'
                
        except (ValueError, TypeError) as e:
            feedback.append(DataQualityFeedback(
                severity='critical',
                field='emissions_data',
                issue=f'Invalid numeric data: {str(e)}',
                recommendation='Ensure all emissions values are valid numbers',
                compliance_impact='Invalid data format prevents XBRL validation'
        
        return feedback
    
    def analyze_water_data(self, data: Dict[str, Any]) -> List[DataQualityFeedback]:
        """Analyze water resource data quality"""
        feedback = []
        
        try:
            consumption = float(data.get('water_consumption', 0))
            withdrawal = float(data.get('water_withdrawal', 0))
            
            if withdrawal > 0 and consumption > withdrawal:
                feedback.append(DataQualityFeedback(
                    severity='critical',
                    field='water_consumption',
                    issue='Water consumption exceeds withdrawal',
                    recommendation='Consumption cannot exceed withdrawal. Consumption = Withdrawal - Discharge. Review water balance calculations.',
                    compliance_impact='Violates basic water accounting principles under ESRS E3'
            
            if withdrawal > 0:
                efficiency = consumption / withdrawal
                if efficiency < self.benchmarks['water_efficiency']['min']:
                    feedback.append(DataQualityFeedback(
                        severity='suggestion',
                        field='water_efficiency',
                        issue=f'Low water consumption ratio ({efficiency*100:.1f}%)',
                        recommendation='High discharge rate may indicate opportunities for water recycling. Consider closed-loop systems or treatment for reuse.',
                        compliance_impact='May indicate incomplete water efficiency measures'
            
            if withdrawal == 0 and consumption == 0:
                feedback.append(DataQualityFeedback(
                    severity='warning',
                    field='water_data',
                    issue='No water data reported',
                    recommendation='If operations use water, report withdrawal and consumption. If truly zero (e.g., office-only operations), add explanatory note.',
                    compliance_impact='Missing data may require explanation under ESRS E3'
                
        except (ValueError, TypeError):
            feedback.append(DataQualityFeedback(
                severity='critical',
                field='water_data',
                issue='Invalid water data format',
                recommendation='Ensure water values are valid numbers in cubic meters (m³)',
                compliance_impact='Invalid data prevents proper XBRL tagging'
        
        return feedback
    
    def analyze_waste_data(self, data: Dict[str, Any]) -> List[DataQualityFeedback]:
        """Analyze circular economy data quality"""
        feedback = []
        
        try:
            generated = float(data.get('waste_generated', 0))
            recycled = float(data.get('waste_recycled', 0))
            
            if recycled > generated:
                feedback.append(DataQualityFeedback(
                    severity='critical',
                    field='waste_recycled',
                    issue='Recycled waste exceeds total generated',
                    recommendation='Recycled amount cannot exceed total waste generated. Review waste tracking methodology.',
                    compliance_impact='Data inconsistency violates ESRS E5 requirements'
            
            if generated > 0:
                recycling_rate = recycled / generated
                if recycling_rate < self.benchmarks['recycling_rate']['min']:
                    feedback.append(DataQualityFeedback(
                        severity='suggestion',
                        field='recycling_rate',
                        issue=f'Low recycling rate ({recycling_rate*100:.1f}%)',
                        recommendation='Consider waste segregation improvements, partnership with recycling facilities, or circular design principles. EU targets 65% recycling by 2035.',
                        compliance_impact='May not meet future regulatory expectations'
            
            if generated == 0:
                feedback.append(DataQualityFeedback(
                    severity='warning',
                    field='waste_generated',
                    issue='No waste generation reported',
                    recommendation='All operations generate some waste. Include all waste streams: hazardous, non-hazardous, e-waste. If truly zero, provide explanation.',
                    compliance_impact='Zero waste claims require substantiation under ESRS E5'
                
        except (ValueError, TypeError):
            feedback.append(DataQualityFeedback(
                severity='critical',
                field='waste_data',
                issue='Invalid waste data format',
                recommendation='Ensure waste values are valid numbers in tonnes',
                compliance_impact='Invalid data prevents XBRL compliance'
        
        return feedback
    
    def analyze_lei_format(self, lei: str) -> List[DataQualityFeedback]:
        """Validate LEI format and structure"""
        feedback = []
        
        # LEI should be 20 alphanumeric characters
        lei_pattern = r'^[A-Z0-9]{20}$'
        clean_lei = lei.replace('LEI:', '').replace(' ', '')
        
        if not re.match(lei_pattern, clean_lei):
            feedback.append(DataQualityFeedback(
                severity='critical',
                field='lei',
                issue='Invalid LEI format',
                recommendation='LEI must be exactly 20 alphanumeric characters. Verify with GLEIF database. Format: XXXXXXXXXXXXXXXXXXXX (no spaces or prefixes in data).',
                compliance_impact='Invalid LEI prevents regulatory submission'
        
        return feedback
    
    def generate_holistic_recommendations(self, all_feedback: List[DataQualityFeedback], data: Dict[str, Any]) -> List[DataQualityFeedback]:
        """Generate holistic recommendations based on overall data quality"""
        critical_count = sum(1 for f in all_feedback if f.severity == 'critical')
        
        if critical_count >= 3:
            all_feedback.append(DataQualityFeedback(
                severity='critical',
                field='overall_data_quality',
                issue='Multiple critical data quality issues detected',
                recommendation='Implement comprehensive ESG data management system. Consider: (1) Automated data collection from source systems, (2) Third-party data validation, (3) Internal audit of calculation methodologies, (4) Staff training on CSRD requirements.',
                compliance_impact='Current data quality insufficient for limited assurance'
        
        # Check for narrative data
        if 'narratives' not in data or not data.get('narratives'):
            all_feedback.append(DataQualityFeedback(
                severity='warning',
                field='narrative_disclosures',
                issue='No narrative disclosures provided',
                recommendation='CSRD requires extensive narrative disclosures. Prepare descriptions for: transition plans, governance, strategy integration, stakeholder engagement, and double materiality assessment process.',
                compliance_impact='Missing mandatory narrative disclosures under ESRS'
        
        return all_feedback
    
    def analyze_data_quality(self, data: Dict[str, Any]) -> List[DataQualityFeedback]:
        """Main entry point for data quality analysis"""
        all_feedback = []
        
        # Analyze each data category
        all_feedback.extend(self.analyze_lei_format(data.get('lei', '')))
        all_feedback.extend(self.analyze_emissions_data(data))
        all_feedback.extend(self.analyze_water_data(data))
        all_feedback.extend(self.analyze_waste_data(data))
        
        # Generate holistic recommendations
        all_feedback = self.generate_holistic_recommendations(all_feedback, data)
        
        # Sort by severity
        severity_order = {'critical': 0, 'warning': 1, 'suggestion': 2}
        all_feedback.sort(key=lambda f: severity_order.get(f.severity, 3))
        
        return all_feedback


class BatchReportGenerator:
    """Production-grade batch processor for XHTML/iXBRL report generation"""
    
    # Required CSV columns
    REQUIRED_COLUMNS = {
        'lei', 'total_emissions', 'scope1_emissions', 
        'scope2_emissions_location', 'scope2_emissions_market',
        'scope3_emissions', 'water_consumption', 'water_withdrawal',
        'waste_generated', 'waste_recycled'
    }
    
    # Default values for optional/missing data
    DEFAULTS = {
        'numeric': '0.0',
        'narrative': 'Data not available for current reporting period.'
    }
    
    def __init__(self, output_base_dir: str = 'output', max_workers: int = 4):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.results: List[ProcessingResult] = []
        self.ai_analyzer = AIDataQualityAnalyzer()
        
    def process_csv_batch(self, csv_path: str) -> Tuple[List[ProcessingResult], str]:
        """
        Main entry point for batch processing
        Returns: (results_list, zip_file_path)
        """
        logger.info(f"Starting batch processing of {csv_path}")
        start_time = datetime.utcnow()
        
        try:
            # Load and validate CSV
            rows = self._load_and_validate_csv(csv_path)
            logger.info(f"Loaded {len(rows)} valid rows from CSV")
            
            # Process rows in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._process_single_company, row, idx): (row, idx)
                    for idx, row in enumerate(rows, 1)
                }
                
                for future in as_completed(futures):
                    row, idx = futures[future]
                    try:
                        result = future.result()
                        self.results.append(result)
                        logger.info(f"Processed {result.lei} - Status: {result.validation_status}")
                    except Exception as e:
                        logger.error(f"Failed to process row {idx}: {str(e)}")
                        self.results.append(ProcessingResult(
                            lei=row.get('lei', 'UNKNOWN'),
                            input_row_number=idx,
                            output_path='',
                            validation_status='error',
                            validation_errors=[str(e)]
            
            # Generate summary report
            summary_path = self._generate_summary_report()
            logger.info(f"Generated summary report: {summary_path}")
            
            # Create ZIP archive
            zip_path = self._create_zip_archive()
            logger.info(f"Created ZIP archive: {zip_path}")
            
            # Calculate stats
            total_time = (datetime.utcnow() - start_time).total_seconds()
            success_count = sum(1 for r in self.results if r.validation_status == 'success')
            logger.info(f"Batch processing complete. {success_count}/{len(self.results)} reports validated successfully in {total_time:.2f}s")
            
            return self.results, zip_path
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise
    
    def _load_and_validate_csv(self, csv_path: str) -> List[Dict[str, str]]:
        """Load CSV and validate structure"""
        rows = []
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or invalid")
            
            missing_columns = self.REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Read and clean rows
            for row_num, row in enumerate(reader, 1):
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Validate LEI
                lei = row.get('lei', '').strip()
                if not lei:
                    logger.warning(f"Row {row_num}: Missing LEI, skipping")
                    continue
                
                # Clean and validate numeric fields
                cleaned_row = {'lei': lei}
                for col in self.REQUIRED_COLUMNS:
                    if col == 'lei':
                        continue
                    
                    value = row.get(col, '').strip()
                    if not value:
                        value = self.DEFAULTS['numeric']
                    
                    # Validate numeric format
                    try:
                        float(value)
                        cleaned_row[col] = value
                    except ValueError:
                        logger.warning(f"Row {row_num}: Invalid numeric value for {col}, using default")
                        cleaned_row[col] = self.DEFAULTS['numeric']
                
                # Add any additional columns (narratives, etc.)
                for col in reader.fieldnames:
                    if col not in self.REQUIRED_COLUMNS and col not in cleaned_row:
                        cleaned_row[col] = row.get(col, '').strip()
                
                rows.append(cleaned_row)
        
        if not rows:
            raise ValueError("No valid rows found in CSV")
        
        return rows
    
    def _process_single_company(self, row: Dict[str, str], row_number: int) -> ProcessingResult:
        """Process a single company's data"""
        start_time = datetime.utcnow()
        lei = row['lei']
        
        try:
            # Run AI data quality analysis
            data_quality_feedback = self.ai_analyzer.analyze_data_quality(row)
            
            # Create output directory for this LEI
            lei_dir = self.output_base_dir / self._sanitize_lei(lei)
            lei_dir.mkdir(parents=True, exist_ok=True)
            
            # Construct voucher data (includes AI suggestions)
            voucher_data = self._construct_voucher_data(row, data_quality_feedback)
            
            # Generate report
            output_path = lei_dir / 'compliance_report.xhtml'
            generate_ixbrl(voucher_data, str(output_path))
            
            # Validate with Arelle
            validation_result = validate_with_arelle(str(output_path))
            
            # Process validation result
            validation_errors = []
            if validation_result.get('status') == 'valid':
                validation_status = 'success'
                # Add critical data quality issues even if XBRL validates
                critical_issues = [f for f in data_quality_feedback if f.severity == 'critical']
                if critical_issues:
                    validation_status = 'failed'
                    validation_errors = [f.to_string() for f in critical_issues]
            else:
                validation_status = 'failed'
                validation_errors = validation_result.get('errors', ['Unknown validation error'])
                # Add data quality feedback to validation errors
                validation_errors.extend([f.to_string() for f in data_quality_feedback if f.severity == 'critical'])
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                lei=lei,
                input_row_number=row_number,
                output_path=str(output_path.relative_to(self.output_base_dir)),
                validation_status=validation_status,
                validation_errors=validation_errors,
                data_quality_feedback=data_quality_feedback,
                processing_time_seconds=processing_time
            
        except Exception as e:
            logger.error(f"Error processing {lei}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            return ProcessingResult(
                lei=lei,
                input_row_number=row_number,
                output_path='',
                validation_status='error',
                validation_errors=[f"Processing error: {str(e)}"],
                data_quality_feedback=data_quality_feedback if 'data_quality_feedback' in locals() else [],
                processing_time_seconds=(datetime.utcnow() - start_time).total_seconds()
    
    def _construct_voucher_data(self, row: Dict[str, str], quality_feedback: List[DataQualityFeedback]) -> Dict[str, Any]:
        """Construct voucher_data dictionary from CSV row with AI enhancements"""
        voucher_data = {
            'lei': row['lei'],
            'report_title': f"CSRD Sustainability Report 2024 - {row['lei']}",
            'total_emissions': row['total_emissions'],
            'scope1_emissions': row['scope1_emissions'],
            'scope2_emissions_location': row['scope2_emissions_location'],
            'scope2_emissions_market': row['scope2_emissions_market'],
            'scope3_emissions': row['scope3_emissions'],
            'water_consumption': row['water_consumption'],
            'water_withdrawal': row['water_withdrawal'],
            'waste_generated': row['waste_generated'],
            'waste_recycled': row['waste_recycled']
        }
        
        # Add calculated fields
        try:
            total_waste = float(row['waste_generated'])
            recycled_waste = float(row['waste_recycled'])
            if total_waste > 0:
                recycling_rate = (recycled_waste / total_waste) * 100
                voucher_data['recycling_rate'] = f"{recycling_rate:.1f}"
            else:
                voucher_data['recycling_rate'] = "0.0"
        except (ValueError, ZeroDivisionError):
            voucher_data['recycling_rate'] = "0.0"
        
        # Add scope 3 category data if available
        for i in range(1, 16):
            cat_key = f'scope3_cat{i}'
            if cat_key in row:
                voucher_data[cat_key] = row[cat_key]
        
        # Add narrative data with AI enhancement
        voucher_data['narratives'] = {
            'transition_plan': row.get('transition_plan_narrative', 
                self._enhance_narrative_with_ai('transition_plan', quality_feedback)),
            'climate_risks': row.get('climate_risks_narrative',
                self._enhance_narrative_with_ai('climate_risks', quality_feedback)),
            'water_strategy': row.get('water_strategy_narrative',
                self._enhance_narrative_with_ai('water_strategy', quality_feedback)),
            'biodiversity_impact': row.get('biodiversity_narrative',
                self._enhance_narrative_with_ai('biodiversity', quality_feedback)),
            'circular_economy': row.get('circular_economy_narrative',
                self._enhance_narrative_with_ai('circular_economy', quality_feedback)),
            'data_quality_statement': self._generate_data_quality_narrative(quality_feedback)
        }
        
        # Add AI feedback summary to metadata
        voucher_data['ai_data_quality_summary'] = {
            'critical_issues': [f.to_string() for f in quality_feedback if f.severity == 'critical'],
            'warnings': [f.to_string() for f in quality_feedback if f.severity == 'warning'],
            'suggestions': [f.to_string() for f in quality_feedback if f.severity == 'suggestion']
        }
        
        return voucher_data
    
    def _enhance_narrative_with_ai(self, narrative_type: str, quality_feedback: List[DataQualityFeedback]) -> str:
        """Generate AI-enhanced narrative based on data quality analysis"""
        base_narratives = {
            'transition_plan': 'We are committed to achieving net-zero emissions by 2040. Our transition plan includes renewable energy adoption, energy efficiency improvements, and supply chain engagement.',
            'climate_risks': 'Climate risk assessment has been conducted identifying both physical and transition risks. Mitigation strategies are being implemented across our operations.',
            'water_strategy': 'Our water management strategy focuses on reduction, recycling, and responsible sourcing, particularly in water-stressed regions.',
            'biodiversity': 'Biodiversity assessments have been conducted at material sites. We are implementing nature-positive strategies aligned with global frameworks.',
            'circular_economy': 'Circular economy principles are being integrated into product design and operations, focusing on waste reduction and material recovery.'
        }
        
        # Find relevant feedback for this narrative type
        relevant_feedback = [f for f in quality_feedback if narrative_type.lower() in f.field.lower() or narrative_type.lower() in f.recommendation.lower()]
        
        base = base_narratives.get(narrative_type, 'Comprehensive measures are being implemented.')
        
        if relevant_feedback:
            # Add AI-suggested improvements
            suggestions = ' '.join([f.recommendation for f in relevant_feedback[:2]])  # Limit to top 2 suggestions
            base += f" Note: Data quality improvements needed - {suggestions}"
        
        return base
    
    def _generate_data_quality_narrative(self, quality_feedback: List[DataQualityFeedback]) -> str:
        """Generate a narrative about data quality and improvement plans"""
        if not quality_feedback:
            return "Data quality assessment indicates full compliance with CSRD reporting requirements."
        
        critical_count = sum(1 for f in quality_feedback if f.severity == 'critical')
        warning_count = sum(1 for f in quality_feedback if f.severity == 'warning')
        
        narrative = "Data quality assessment identified areas for improvement. "
        
        if critical_count > 0:
            narrative += f"{critical_count} critical issues require immediate attention to ensure CSRD compliance. "
        
        if warning_count > 0:
            narrative += f"{warning_count} warnings indicate opportunities for enhanced data quality. "
        
        narrative += "We are implementing enhanced data collection and validation processes to address these findings."
        
        return narrative
    
    def _sanitize_lei(self, lei: str) -> str:
        """Sanitize LEI for use as folder name"""
        # Remove any characters that might cause filesystem issues
        sanitized = lei.replace(':', '_').replace('/', '_').replace('\\', '_')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in ('_', '-'))
        return sanitized[:50]  # Limit length
    
    def _generate_summary_report(self) -> str:
        """Generate CSV summary report of all processed files"""
        summary_path = self.output_base_dir / 'report_log.csv'
        
        with open(summary_path, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                fieldnames = list(self.results[0].to_csv_row().keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in sorted(self.results, key=lambda r: r.lei):
                    writer.writerow(result.to_csv_row())
        
        # Also generate JSON report for programmatic access
        json_path = self.output_base_dir / 'report_log.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            # Convert data quality feedback to serializable format
            serializable_results = []
            for result in self.results:
                result_dict = asdict(result)
                result_dict['data_quality_feedback'] = [
                    {
                        'severity': f.severity,
                        'field': f.field,
                        'issue': f.issue,
                        'recommendation': f.recommendation,
                        'compliance_impact': f.compliance_impact
                    }
                    for f in result.data_quality_feedback
                ]
                serializable_results.append(result_dict)
            
            json.dump({
                'processing_summary': {
                    'total_processed': len(self.results),
                    'successful': sum(1 for r in self.results if r.validation_status == 'success'),
                    'failed': sum(1 for r in self.results if r.validation_status == 'failed'),
                    'errors': sum(1 for r in self.results if r.validation_status == 'error'),
                    'total_critical_issues': sum(len([f for f in r.data_quality_feedback if f.severity == 'critical']) for r in self.results),
                    'total_warnings': sum(len([f for f in r.data_quality_feedback if f.severity == 'warning']) for r in self.results),
                    'timestamp': datetime.utcnow().isoformat()
                },
                'results': serializable_results
            }, f, indent=2)
        
        return str(summary_path)
    
    def _create_zip_archive(self) -> str:
        """Create ZIP file of all generated reports"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        zip_path = self.output_base_dir.parent / f'csrd_reports_{timestamp}.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all files in output directory
            for file_path in self.output_base_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.output_base_dir.parent)
                    zf.write(file_path, arcname)
        
        # Calculate checksum
        checksum = self._calculate_file_checksum(zip_path)
        checksum_path = zip_path.with_suffix('.zip.sha256')
        checksum_path.write_text(f"{checksum}  {zip_path.name}\n")
        
        return str(zip_path)
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def main(csv_path: str, output_dir: str = 'output', max_workers: int = 4) -> Tuple[List[ProcessingResult], str]:
    """
    Main entry point for batch processing
    
    Args:
        csv_path: Path to input CSV file
        output_dir: Base directory for output files
        max_workers: Maximum parallel workers
    
    Returns:
        Tuple of (results_list, zip_file_path)
    """
    generator = BatchReportGenerator(output_dir, max_workers)
    return generator.process_csv_batch(csv_path)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch generate CSRD/ESRS iXBRL reports with AI-powered data quality analysis')
    parser.add_argument('csv_file', help='Input CSV file path')
    parser.add_argument('--output-dir', default='output', help='Output directory (default: output)')
    parser.add_argument('--max-workers', type=int, default=4, help='Max parallel workers (default: 4)')
    
    args = parser.parse_args()
    
    try:
        results, zip_path = main(args.csv_file, args.output_dir, args.max_workers)
        print(f"\nProcessing complete!")
        print(f"Reports generated: {len(results)}")
        print(f"Successful validations: {sum(1 for r in results if r.validation_status == 'success')}")
        print(f"Critical data quality issues: {sum(len([f for f in r.data_quality_feedback if f.severity == 'critical']) for r in results)}")
        print(f"Archive created: {zip_path}")
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        sys.exit(1)
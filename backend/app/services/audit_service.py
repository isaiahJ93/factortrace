# backend/app/services/audit_service.py

from typing import Dict, Any, Optional
import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import EmissionCalculationAudit, DataLineage

class AuditService:
    """Comprehensive audit trail for GHG calculations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_calculation(
        self,
        calculation_id: str,
        user_id: str,
        organization_id: str,
        calculation_data: Dict[str, Any],
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmissionCalculationAudit:
        """Log complete calculation with traceability"""
        
        # Generate hashes for integrity
        input_hash = self._generate_hash(calculation_data)
        calc_hash = self._generate_hash({
            **calculation_data,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        audit_entry = EmissionCalculationAudit(
            calculation_id=calculation_id,
            user_id=user_id,
            organization_id=organization_id,
            action='calculate',
            scope=calculation_data['scope'],
            category=calculation_data.get('category'),
            activity_data=json.dumps(calculation_data['activity_data']),
            emission_factor_id=calculation_data['emission_factor_id'],
            result_tco2e=result['emissions'],
            uncertainty_range=json.dumps({
                'lower': str(result['confidence_interval_lower']),
                'upper': str(result['confidence_interval_upper']),
                'confidence_level': result['confidence_level']
            }),
            data_quality_score=result['data_quality_score'],
            calculation_method=calculation_data['method'],
            allocation_method=calculation_data.get('allocation_method'),
            calculation_hash=calc_hash,
            input_data_hash=input_hash,
            reporting_period=metadata.get('reporting_period'),
            esrs_paragraph=metadata.get('esrs_paragraph'),
            taxonomy_element=metadata.get('taxonomy_element')
        )
        
        self.db.add(audit_entry)
        self.db.commit()
        
        return audit_entry
    
    def add_data_lineage(
        self,
        audit_id: int,
        source_type: str,
        source_id: str,
        source_date: datetime,
        data_owner: str,
        collection_method: str,
        transformation_applied: Optional[str] = None,
        quality_checks: Optional[Dict[str, Any]] = None
    ):
        """Track data source and transformations"""
        
        lineage = DataLineage(
            emission_calculation_audit_id=audit_id,
            source_type=source_type,
            source_id=source_id,
            source_date=source_date,
            data_owner=data_owner,
            collection_method=collection_method,
            transformation_applied=transformation_applied,
            quality_checks=json.dumps(quality_checks) if quality_checks else None
        )
        
        self.db.add(lineage)
        self.db.commit()
    
    def _generate_hash(self, data: Dict[str, Any]) -> str:
        """Generate SHA-256 hash of data"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
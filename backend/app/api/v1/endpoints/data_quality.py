from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.emission import Emission
from app.models.emission_factor import EmissionFactor

router = APIRouter()

def calculate_data_quality_score(emission: Emission) -> Dict[str, float]:
    """Calculate comprehensive data quality score for an emission entry."""
    
    # Base scores for evidence types
    evidence_scores = {
        'invoice': 100,
        'receipt': 100,
        'photo': 90,
        'meter_reading': 95,
        'estimate': 70,
        'none': 50
    }
    
    # 1. Accuracy Score (30% weight) - Based on evidence type
    accuracy_score = evidence_scores.get(emission.evidence_type or 'none', 50)
    
    # 2. Completeness Score (25% weight) - Check required fields
    required_fields = ['emission_factor_id', 'activity_data', 'amount']
    optional_fields = ['description', 'location', 'evidence_type', 'document_url']
    
    filled_required = sum(1 for field in required_fields if getattr(emission, field, None) is not None)
    filled_optional = sum(1 for field in optional_fields if getattr(emission, field, None) is not None)
    
    completeness_score = (
        (filled_required / len(required_fields)) * 70 +
        (filled_optional / len(optional_fields)) * 30
    )
    
    # 3. Timeliness Score (20% weight) - How recent is the data
    if emission.created_at:
        days_old = (datetime.now().date() - emission.created_at.date()).days
        if days_old <= 30:
            timeliness_score = 100
        elif days_old <= 90:
            timeliness_score = 80
        elif days_old <= 180:
            timeliness_score = 60
        else:
            timeliness_score = 40
    else:
        timeliness_score = 30
    
    # 4. Consistency Score (25% weight) - Placeholder for now
    # In production, compare with similar emissions
    consistency_score = 85
    
    # Calculate weighted total
    total_score = (
        accuracy_score * 0.30 +
        completeness_score * 0.25 +
        timeliness_score * 0.20 +
        consistency_score * 0.25
    )
    
    return {
        'total_score': round(total_score, 1),
        'accuracy_score': round(accuracy_score, 1),
        'completeness_score': round(completeness_score, 1),
        'timeliness_score': round(timeliness_score, 1),
        'consistency_score': round(consistency_score, 1),
        'evidence_type': emission.evidence_type or 'none'
    }

@router.get("/data-quality")
async def get_emissions_quality(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all emissions with their data quality scores."""
    emissions = db.query(Emission).offset(skip).limit(limit).all()
    
    results = []
    for emission in emissions:
        quality_score = calculate_data_quality_score(emission)
        results.append({
            'id': emission.id,
            'date': emission.created_at,
            'amount': emission.emission_amount,
            'quality_score': quality_score
        })
    
    return results

@router.get("/data-quality/{emission_id}")
async def get_emission_quality(
    emission_id: int,
    db: Session = Depends(get_db)
):
    """Get data quality score for a specific emission."""
    emission = db.query(Emission).filter(Emission.id == emission_id).first()
    if not emission:
        raise HTTPException(status_code=404, detail="Emission not found")
    
    return calculate_data_quality_score(emission)

@router.post("/improve-quality/{emission_id}")
async def improve_quality_suggestions(
    emission_id: int,
    db: Session = Depends(get_db)
):
    """Get suggestions to improve data quality score."""
    emission = db.query(Emission).filter(Emission.id == emission_id).first()
    if not emission:
        raise HTTPException(status_code=404, detail="Emission not found")
    
    scores = calculate_data_quality_score(emission)
    suggestions = []
    
    # Accuracy suggestions
    if scores['accuracy_score'] < 90:
        suggestions.append({
            'category': 'accuracy',
            'impact': 'high',
            'suggestion': 'Upload an invoice or receipt for maximum accuracy',
            'potential_improvement': 100 - scores['accuracy_score']
        })
    
    # Completeness suggestions
    if scores['completeness_score'] < 90:
        missing_fields = []
        if not emission.description:
            missing_fields.append('description')
        if not emission.location:
            missing_fields.append('location')
        
        suggestions.append({
            'category': 'completeness',
            'impact': 'medium',
            'suggestion': f'Fill in missing fields: {", ".join(missing_fields)}',
            'potential_improvement': 100 - scores['completeness_score']
        })
    
    # Timeliness suggestions
    if scores['timeliness_score'] < 80:
        suggestions.append({
            'category': 'timeliness',
            'impact': 'medium',
            'suggestion': 'Update with more recent data if available',
            'potential_improvement': 100 - scores['timeliness_score']
        })
    
    return {
        'current_scores': scores,
        'suggestions': suggestions
    }
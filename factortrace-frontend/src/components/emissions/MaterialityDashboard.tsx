// frontend/src/components/emissions/MaterialityDashboard.tsx

import React, { useEffect, useState } from 'react';
import { assessMateriality } from '@/api/emissions';

export const MaterialityDashboard: React.FC = () => {
  const [sector, setSector] = useState('Manufacturing');
  const [assessments, setAssessments] = useState<any[]>([]);

  useEffect(() => {
    loadMateriality();
  }, [sector]);

  const loadMateriality = async () => {
    const response = await assessMateriality(sector);
    setAssessments(response.assessments);
  };

  return (
    <div className="materiality-dashboard">
      <h2>Scope 3 Materiality Assessment</h2>
      
      <select value={sector} onChange={(e) => setSector(e.target.value)}>
        <option value="Manufacturing">Manufacturing</option>
        <option value="Retail">Retail</option>
        <option value="Technology">Technology</option>
        <option value="Finance">Finance</option>
      </select>

      <div className="materiality-grid">
        {assessments.map((assessment) => (
          <div 
            key={assessment.category} 
            className={`category-card ${assessment.is_material ? 'material' : 'not-material'}`}
          >
            <h3>{assessment.category_name}</h3>
            <span className="badge">{assessment.is_material ? 'MATERIAL' : 'NOT MATERIAL'}</span>
            <p>Threshold: {assessment.threshold}%</p>
            <p>Data availability: {assessment.data_availability}</p>
            <ul>
              {assessment.recommendations.map((rec: string, idx: number) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};
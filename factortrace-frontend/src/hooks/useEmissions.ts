import { useState, useEffect, useCallback } from 'react';
import { emissionAPI, emissionWS } from '../services/api';
import type { Emission } from '../services/api.types';

interface UseEmissionsReturn {
  emissions: Emission[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useEmissions = (scope: number = 3): UseEmissionsReturn => {
  const [emissions, setEmissions] = useState<Emission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEmissions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await emissionAPI.getEmissions(scope);
      setEmissions(data.emissions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch emissions');
    } finally {
      setLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    fetchEmissions();

    // Set up WebSocket connection
    emissionWS.connect();
    
    const handleEvidenceUpdate = (data: any) => {
      setEmissions(prev => prev.map(emission => 
        emission.id === data.emissionId 
          ? { ...emission, evidenceCount: emission.evidenceCount + 1 }
          : emission
      ));
    };

    emissionWS.on('evidence:uploaded', handleEvidenceUpdate);

    return () => {
      emissionWS.off('evidence:uploaded', handleEvidenceUpdate);
      emissionWS.disconnect();
    };
  }, [fetchEmissions]);

  return { emissions, loading, error, refetch: fetchEmissions };
};
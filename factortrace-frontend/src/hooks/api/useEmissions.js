import { useState, useEffect } from 'react';
import { emissionAPI, emissionWS } from '../services/api';

export const useEmissions = (scope = 3) => {
  const [emissions, setEmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEmissions = async () => {
      try {
        setLoading(true);
        const data = await emissionAPI.getEmissions(scope);
        setEmissions(data.emissions);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchEmissions();

    // Set up WebSocket listeners
    emissionWS.connect();
    emissionWS.on('evidence:uploaded', (data) => {
      setEmissions(prev => prev.map(emission => 
        emission.id === data.emissionId 
          ? { ...emission, evidenceCount: emission.evidenceCount + 1 }
          : emission
      ));
    });

    return () => {
      emissionWS.disconnect();
    };
  }, [scope]);

  return { emissions, loading, error, refetch: () => fetchEmissions() };
};
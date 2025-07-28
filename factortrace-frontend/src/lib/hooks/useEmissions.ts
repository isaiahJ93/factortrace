import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { emissionsApi } from '@/lib/api/emissions';
import { EmissionCreate } from '@/lib/types/emissions';
import { toast } from 'sonner';

export function useEmissions(filters?: any) {
  return useQuery({
    queryKey: ['emissions', filters],
    queryFn: () => emissionsApi.getEmissions(filters),
  });
}

export function useEmissionsSummary() {
  return useQuery({
    queryKey: ['emissions-summary'],
    queryFn: () => emissionsApi.getEmissionsSummary(),
  });
}

export function useCreateEmissionsBatch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (emissions: EmissionCreate[]) => emissionsApi.createEmissionsBatch(emissions),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['emissions'] });
      queryClient.invalidateQueries({ queryKey: ['emissions-summary'] });
      toast.success(`Successfully recorded ${data.length} emission entries`);
    },
    onError: (error) => {
      toast.error('Failed to record emissions');
      console.error(error);
    },
  });
}
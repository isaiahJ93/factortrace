import { QueryClient } from '@tanstack/react-query';

export class CacheStrategy {
  constructor(private queryClient: QueryClient) {}
  
  /**
   * Implement stale-while-revalidate with background updates
   */
  setupBackgroundRefetch() {
    // Refetch queries that are stale but still in view
    setInterval(() => {
      const queries = this.queryClient.getQueryCache().getAll();
      
      queries.forEach(query => {
        const state = query.state;
        if (
          state.status === 'success' &&
          state.isInvalidated &&
          query.getObserversCount() > 0
        ) {
          query.fetch();
        }
      });
    }, 10000); // Every 10 seconds
  }
  
  /**
   * Implement optimistic updates with conflict resolution
   */
  optimisticUpdate<T>(
    queryKey: any[],
    updater: (old: T) => T,
    rollbackFn?: (error: Error, variables: any, context: any) => void
  ) {
    const previousData = this.queryClient.getQueryData<T>(queryKey);
    
    // Optimistic update
    this.queryClient.setQueryData<T>(queryKey, updater);
    
    return {
      previousData,
      rollback: () => {
        this.queryClient.setQueryData(queryKey, previousData);
      },
    };
  }
  
  /**
   * Implement cache warming for predictive fetching
   */
  async warmCache(predictions: Array<{ queryKey: any[]; queryFn: () => Promise<any> }>) {
    const promises = predictions.map(({ queryKey, queryFn }) =>
      this.queryClient.prefetchQuery({
        queryKey,
        queryFn,
        staleTime: 5 * 60 * 1000, // 5 minutes
      })
    );
    
    await Promise.allSettled(promises);
  }
}

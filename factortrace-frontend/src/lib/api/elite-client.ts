export const eliteAPI = {
  emissions: {
    list: async () => ({ data: [] }),
    create: async (data: any) => ({ data }),
    update: async (id: string, data: any) => ({ data }),
    delete: async (id: string) => {},
    summary: async () => ({ data: { scope1_total: 0, scope2_total: 0, scope3_total: 0, total_emissions: 0 } })
  }
};

export const emissionsKeys = {
  all: ['emissions'] as const,
  lists: () => [...emissionsKeys.all, 'list'] as const,
  list: (params?: any) => [...emissionsKeys.lists(), params] as const,
  details: () => [...emissionsKeys.all, 'detail'] as const,
  detail: (id: string) => [...emissionsKeys.details(), id] as const,
};

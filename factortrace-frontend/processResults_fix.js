  const processResults = (apiData: any, activeActivities: any[]) => {
    const summary = apiData.summary;
    
    // Enhanced breakdown with correct field mapping
    const enhancedBreakdown = apiData.breakdown.map((item: any) => {
      const activity = activeActivities.find(a => 
        a.optionId === item.activity_type || 
        a.name?.toLowerCase() === item.activity_type?.toLowerCase()
      );
      
      return {
        ...item,
        ...activity,
        emissions_tons: item.emissions_kg_co2e / 1000,
        categoryName: activity?.categoryName || item.activity_type,
        scopeId: item.scope,
        categoryId: item.scope
      };
    });
    
    // Simplified category totals
    const categoryTotals = enhancedBreakdown.reduce((acc: any, item: any) => {
      const key = item.activity_type;
      if (!acc[key]) {
        acc[key] = {
          scope: item.scope,
          category: item.activity_type,
          activity_type: item.activity_type,
          emissions: 0,
          emissions_kg_co2e: 0,
          items: []
        };
      }
      acc[key].emissions += item.emissions_tons;
      acc[key].emissions_kg_co2e += item.emissions_kg_co2e;
      acc[key].items.push(item);
      return acc;
    }, {});
    
    return {
      ...apiData,
      enhancedBreakdown,
      categoryTotals: Object.values(categoryTotals).sort((a: any, b: any) => b.emissions - a.emissions),
      chartData: prepareChartData(summary, categoryTotals)
    };
  };

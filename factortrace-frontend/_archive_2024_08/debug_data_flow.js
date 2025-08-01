// Add this to calculateEmissions after line 386:
console.log("=== DATA FLOW DEBUG ===");
console.log("1. Raw API Response:", data);
console.log("2. Active Activities:", activeActivities);

// Add this to processResults at the beginning:
console.log("3. ProcessResults Input:", apiData);
console.log("4. Breakdown items:", apiData.breakdown);

// Add this in prepareChartData:
console.log("5. CategoryTotals structure:", categoryTotals);
console.log("6. First category item:", Object.values(categoryTotals)[0]);

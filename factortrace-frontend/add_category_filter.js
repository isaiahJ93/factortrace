// Add this to your fetchFactors function:
const fetchFactors = async () => {
  try {
    // Add category parameter
    const url = selectedCategory 
      ? `http://localhost:8000/api/v1/emission-factors?scope=${selectedScope}&category=${selectedCategory}`
      : `http://localhost:8000/api/v1/emission-factors?scope=${selectedScope}`;
      
    const response = await fetch(url);
    if (response.ok) {
      const data = await response.json();
      setFactors(data);
    }
  } catch (err) {
    console.error('Failed to fetch factors:', err);
  }
};

// Add state for selected category:
const [selectedCategory, setSelectedCategory] = useState('');

// Add category selector UI after scope selector

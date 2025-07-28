// Test your API connection
import { emissionAPI } from './api';

export const testAPIConnection = async () => {
  try {
    console.log('Testing API connection...');
    const emissions = await emissionAPI.getEmissions(3);
    console.log('✅ API Connected! Found', emissions.length, 'emissions');
    return true;
  } catch (error) {
    console.error('❌ API Connection Failed:', error);
    return false;
  }
};

// Run in browser console: testAPIConnection()

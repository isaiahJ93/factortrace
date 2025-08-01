// Add this to your browser console before testing
window.addEventListener('click', (e) => {
  if (e.target.textContent?.includes('iXBRL') || e.target.textContent?.includes('Export')) {
    console.log('Export button clicked:', e.target);
  }
});

// Override fetch to log requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
  console.log('Fetch called:', args[0]);
  return originalFetch.apply(this, args)
    .then(response => {
      console.log('Fetch response:', response.status, response.url);
      return response;
    });
};

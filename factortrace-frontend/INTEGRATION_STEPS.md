# FactorTrace Evidence Upload Integration Steps

## 1. Review your current component
Compare src/components/EvidenceUpload.tsx with the new implementation

## 2. Choose integration approach:

### Option A: Replace existing component
```bash
mv src/components/EvidenceUpload.tsx src/components/EvidenceUpload.old.tsx
# Then copy the new component
```

### Option B: Run components side-by-side
```bash
# Keep both and import the enhanced version where needed
import EvidenceUploadEnhanced from './components/EvidenceUploadEnhanced';
```

## 3. Update your backend URL
Edit `.env.local` with your actual API endpoint

## 4. Test the connection
In your browser console:
```javascript
import { testAPIConnection } from './services/api.test';
testAPIConnection();
```

## 5. Update imports in your app
Replace imports of EvidenceUpload with the enhanced version

## Next: Your backend needs these endpoints:
- GET    /api/v1/emissions
- POST   /api/v1/emissions/{id}/evidence  
- GET    /api/v1/emissions/{id}/evidence
- DELETE /api/v1/emissions/{id}/evidence/{id}
- POST   /api/v1/audit/logs
- WSS    /emissions/sync

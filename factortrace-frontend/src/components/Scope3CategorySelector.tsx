// frontend/src/app/emissions/components/Scope3CategorySelector.tsx
import { SCOPE3_CATEGORIES } from '@/constants/scope3Categories';

export const Scope3CategorySelector: React.FC = () => {
  return (
    <select className="form-select">
      {Object.entries(SCOPE3_CATEGORIES).map(([key, category]) => (
        <option key={key} value={key}>
          {category.displayName} ({category.ghgProtocolId})
        </option>
      ))}
    </select>
  );
};
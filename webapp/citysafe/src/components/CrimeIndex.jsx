import { useEffect, useState } from 'react';
import http from '../api/http';
import '../styles/CrimeIndex.scss';

export default function CrimeIndex({ neighborhoodId }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!neighborhoodId) return;
    http.get(`/neighborhoods/${neighborhoodId}/crime_count`)
      .then(res => setCount(res.data.count))
      .catch(() => setCount(0));
  }, [neighborhoodId]);

  const MAX = 1200;
  const pct = Math.min(100, (count / MAX) * 100);

  return (
    <div className="crime-index">
      <h4>Indice de criminalité</h4>
      <div className="bar">
        <div 
          className="marker" 
          style={{ left: `${pct}%` }} 
          title={`${count} crimes`} 
        />
      </div>
      <div className="legend">
        <span>Peu</span><span>Modéré</span><span>Beaucoup</span>
      </div>
    </div>
  );
}

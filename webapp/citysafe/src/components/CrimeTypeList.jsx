import { useEffect, useState } from 'react';
import { fetchCrimeTypeCounts } from '../api/complaintsApi';
import styles from '../styles/CrimeTypeList.module.scss';

export default function CrimeTypeList({ neighborhoodId }) {
  const [types, setTypes] = useState([]);

  useEffect(() => {
    if (!neighborhoodId) return;
    fetchCrimeTypeCounts(neighborhoodId)
      .then(setTypes)
      .catch(() => setTypes([]));
  }, [neighborhoodId]);

  if (types.length === 0) return null;

  return (
    <div className={styles.container}>
      <h4 className={styles.heading}>Types de crimes</h4>
      <ul className={styles.list}>
        {types.slice(0, 5).map(({ type, count }) => (
          <li key={type} className={styles.item}>
            <span className={styles.type}>{type}</span>
            <span className={styles.badge}>{count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

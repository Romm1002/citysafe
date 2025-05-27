import { useEffect, useState } from 'react';
import styles from '../styles/CrimePopup.module.scss';
import { fetchNeighborhood } from '../api/neighborhoodsApi';
import CrimeIndex from './CrimeIndex';

export default function CrimePopup({ neighborhoodId, onClose }) {
  const [neighborhood, setNeighborhood] = useState(null);

  useEffect(() => {
    if (!neighborhoodId) {
      setNeighborhood(null);
      return;
    }
    fetchNeighborhood(neighborhoodId)
      .then(data => setNeighborhood(data))
      .catch(() => setNeighborhood(null));
  }, [neighborhoodId]);

  if (!neighborhood) return null;

  return (
    <div className={styles.neighborhoodPopup}>
      <button className={styles.popupClose} onClick={onClose}>×</button>
      <h3 className={styles.title}>{neighborhood.name} dans {neighborhood.boro}</h3>
      <CrimeIndex neighborhoodId={neighborhoodId} />
    </div>
  );
}

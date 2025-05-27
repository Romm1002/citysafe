import { useState, useEffect } from 'react';
import Search       from '../components/SearchBar';
import Filters      from '../components/Filters';
import MapView      from '../components/MapView';
import CrimePopup   from '../components/CrimePopup';
import { fetchNeighborhoods } from '../api/neighborhoodsApi';
import '../styles/global.scss';

export default function Home() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState(null);
  const [nameToIdMap, setNameToIdMap]                   = useState(null);

  useEffect(() => {
    fetchNeighborhoods().then(list => {
      const map = {};
      list.forEach(n => {
        map[n.name.trim()] = n.id;
      });
      console.log('⛓️ nameToIdMap ready:', map);
      setNameToIdMap(map);
    });
  }, []);

  const handleNeighborhoodClick = dbId => {
    setSelectedNeighborhood(dbId);
  };
  const closePopup = () => setSelectedNeighborhood(null);

  if (nameToIdMap === null) {
    return <div>Chargement des quartiers…</div>;
  }

  return (
    <div className="app-container">
      <header className="controls">
        <div className="logo"><img src="/logo.png" alt="CitySafe" /></div>
        <div className="controls-items"><Search /><Filters /></div>
      </header>

      <CrimePopup
        neighborhoodId={selectedNeighborhood}
        onClose={closePopup}
      />

      <div className="map-wrapper">
        <MapView
          onNeighborhoodClick={handleNeighborhoodClick}
          selectedNeighborhood={selectedNeighborhood}
          nameToIdMap={nameToIdMap}
        />
      </div>
    </div>
  );
}

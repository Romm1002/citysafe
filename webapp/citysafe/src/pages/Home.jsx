import { useState } from 'react';
import Search from '../components/SearchBar';
import Filters from '../components/Filters';
import MapView from '../components/MapView';
import '../styles/global.scss';

export default function Home() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState(null);

  const handleNeighborhoodClick = (props) => {
    setSelectedNeighborhood(props);
  };
  const closePopup = () => setSelectedNeighborhood(null);

  return (
    <div className="app-container">
      <header className="controls">
        <div className="logo">
          <img src="/logo.png" alt="CitySafe" />
        </div>
        <div className="controls-items"> 
          <Search />
          <Filters />
        </div>
      </header>

      {selectedNeighborhood && (
        <div className="neighborhood-popup">
          <button className="popup-close" onClick={closePopup}>×</button>
          <h3>{selectedNeighborhood.NTAName}</h3>
          <p><strong>Arrondissement :</strong> {selectedNeighborhood.BoroName}</p>
          <p><strong>Code NTA :</strong> {selectedNeighborhood.NTA2020}</p>
        </div>
      )}

      <div className="map-wrapper">
        <MapView
          onNeighborhoodClick={handleNeighborhoodClick}
        />
      </div>
    </div>
  );
}

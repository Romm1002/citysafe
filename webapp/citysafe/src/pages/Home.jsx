import { useState } from 'react';
import Search from '../components/SearchBar';
import Filters from '../components/Filters';
import MapView from '../components/MapView';
import CrimePopup from '../components/CrimePopup';
import '../styles/global.scss';

export default function Home() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState(null);

  const handleNeighborhoodClick = (props) => {
    setSelectedNeighborhood(props);
  };
  const closePopup = () => {
    setSelectedNeighborhood(null);
  };

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

      <CrimePopup
        neighborhood={selectedNeighborhood}
        onClose={closePopup}
      />

      <div className="map-wrapper">
        <MapView
          onNeighborhoodClick={handleNeighborhoodClick}
          selectedNeighborhood={selectedNeighborhood} 
        />
      </div>
    </div>
  );
}

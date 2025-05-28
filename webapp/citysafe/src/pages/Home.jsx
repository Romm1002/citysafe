import { useState, useEffect } from 'react';
import SearchBar    from '../components/SearchBar';
import Filters      from '../components/Filters';
import MapView      from '../components/MapView';
import CrimePopup   from '../components/CrimePopup';
import Top5Popup    from '../components/Top5Popup';
import { fetchNeighborhoods } from '../api/neighborhoodsApi';
import {
  fetchCrimeTypes,
  fetchTopNeighborhoods
} from '../api/complaintsApi';
import '../styles/global.scss';

export default function Home() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState(null);
  const [nameToIdMap, setNameToIdMap]                   = useState(null);
  const [searchName, setSearchName]                     = useState('');

  const [crimeTypes, setCrimeTypes]                     = useState([]);
  const [selectedCrimeType, setSelectedCrimeType]       = useState('');
  const [top5, setTop5]                                 = useState([]);

  useEffect(() => {
    fetchNeighborhoods().then(list => {
      const m = {};
      list.forEach(n => m[n.name.trim()] = n.id);
      setNameToIdMap(m);
    });
  }, []);

  useEffect(() => {
    fetchCrimeTypes().then(setCrimeTypes);
  }, []);

  useEffect(() => {
    if (!selectedCrimeType) {
      setTop5([]);
      return;
    }
    fetchTopNeighborhoods(selectedCrimeType).then(setTop5);
  }, [selectedCrimeType]);

  const handleNeighborhoodClick = dbId => {
    setSearchName('');
    setSelectedCrimeType('');
    setSelectedNeighborhood(dbId);
  };
  const handleSearch = name => setSearchName(name.trim());
  const handleCrimeTypeChange = type => {
    setSelectedCrimeType(type);
    setSelectedNeighborhood(null);
  };
  const closePopup    = ()   => {
    setSearchName('');
    setSelectedNeighborhood(null);
  }
  const closeTop5     = ()   => setSelectedCrimeType('');

  if (nameToIdMap === null) {
    return <div className="loading">Chargement des quartiers…</div>;
  }

  return (
    <div className="app-container">
      <header className="controls">
        <div className="logo"><img src="/logo.png" alt="CitySafe" /></div>
        <div className="controls-items">
          <SearchBar onSearch={handleSearch} value={searchName} />
          <Filters
            crimeTypes={crimeTypes}
            selectedType={selectedCrimeType}
            onTypeChange={handleCrimeTypeChange}
          />
        </div>
      </header>

      <CrimePopup
        neighborhoodId={selectedNeighborhood}
        onClose={closePopup}
      />

      <Top5Popup
        title={`Top 5 quartiers pour ${selectedCrimeType}`}
        items={top5}
        onClose={closeTop5}
      />

      <div className="map-wrapper">
        <MapView
          onNeighborhoodClick={handleNeighborhoodClick}
          selectedNeighborhood={selectedNeighborhood}
          nameToIdMap={nameToIdMap}
          searchName={searchName}
        />
      </div>
    </div>
  );
}

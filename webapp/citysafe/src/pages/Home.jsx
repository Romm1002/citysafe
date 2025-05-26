import MapView from '../components/MapView';
import '../styles/global.scss';

export default function Home() {
  return (
    <div className="app-container">
      <div className="controls">
        <div className="logo">
          <img src="/logo.png" alt="CitySafe logo" />
        </div>
        <div className="controls-items">
          {/* <SearchBar /> */}
          {/* <Filters /> */}
        </div>
      </div>
      <div className="map-wrapper">
        <MapView />
      </div>
    </div>
  );
}

import { useRef } from 'react';
import useMapbox from '../hooks/useMapbox';
import Tooltip   from './Tooltip';
import '../styles/MapView.scss';

export default function MapView({ onNeighborhoodClick, selectedNeighborhood, nameToIdMap, searchName }) {
  const mapContainer = useRef(null);
  const tooltip      = useRef(null);

  useMapbox({
    containerRef: mapContainer,
    tooltipRef: tooltip, onNeighborhoodClick, selectedNeighborhood, nameToIdMap, searchName
  });

  return (
    <>
      <div ref={mapContainer} className="map-container" />
      <Tooltip ref={tooltip} />
    </>
  );
}

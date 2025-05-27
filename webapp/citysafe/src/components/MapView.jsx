import { useRef } from 'react';
import useMapbox from '../hooks/useMapbox';
import Tooltip   from './Tooltip';
import '../styles/MapView.scss';

export default function MapView({ onNeighborhoodClick, selectedNeighborhood }) {
  const mapContainer = useRef();
  const tooltip      = useRef();

  useMapbox({
    containerRef: mapContainer,
    tooltipRef: tooltip, onNeighborhoodClick, selectedNeighborhood
  });

  return (
    <>
      <div ref={mapContainer} className="map-container" />
      <Tooltip ref={tooltip} />
    </>
  );
}

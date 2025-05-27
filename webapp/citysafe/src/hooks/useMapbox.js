import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import { MAP_STYLE, MAP_BOUNDS, START_VIEW, SOURCE_ID, GEOJSON_URL, LAYERS, MAPBOX_TOKEN } from '../config/mapConfig';

mapboxgl.accessToken = MAPBOX_TOKEN;

export default function useMapbox({
  containerRef,
  tooltipRef,
  onNeighborhoodClick,
  selectedNeighborhood
}) {
  const map = useRef(null);
  const hoveredId  = useRef(null);
  const selectedId = useRef(null);

  // Init map + layers once
  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: containerRef.current,
      style:     MAP_STYLE,
      ...START_VIEW,
      maxBounds: MAP_BOUNDS
    });

    map.current.on('load', () => {
      map.current.addSource(SOURCE_ID, { type: 'geojson', data: GEOJSON_URL });

      // add layers in the right order
        map.current.addLayer({ 
            ...LAYERS.fill, 
            source: SOURCE_ID 
        });
      map.current.addLayer({ ...LAYERS.outline, source: SOURCE_ID });
      map.current.addLayer({ ...LAYERS.label,   source: SOURCE_ID });

      // Hover handlers
      map.current.on('mousemove', LAYERS.fill.id, onMouseMove);
      map.current.on('mouseleave', LAYERS.fill.id, onMouseLeave);

      // Click handler
      map.current.on('click', LAYERS.fill.id, onClickFeature);
    });

    function onMouseMove(e) {
      if (!e.features.length) return;
      // clear old hover
      if (hoveredId.current !== null) {
        map.current.setFeatureState(
          { source: SOURCE_ID, id: hoveredId.current },
          { hover: false }
        );
      }
      hoveredId.current = e.features[0].id;
      map.current.setFeatureState(
        { source: SOURCE_ID, id: hoveredId.current },
        { hover: true }
      );
      // tooltip
      tooltipRef.current.style.display = 'block';
      tooltipRef.current.innerText   = e.features[0].properties.NTAName;
      tooltipRef.current.style.left  = `${e.point.x + 10}px`;
      tooltipRef.current.style.top   = `${e.point.y + 10}px`;
    }

    function onMouseLeave() {
      if (hoveredId.current !== null) {
        map.current.setFeatureState(
          { source: SOURCE_ID, id: hoveredId.current },
          { hover: false }
        );
      }
      hoveredId.current = null;
      tooltipRef.current.style.display = 'none';
    }

    function onClickFeature(e) {
      if (!e.features.length) return;
      const id = e.features[0].id;

      // clear old selection
      if (selectedId.current !== null) {
        map.current.setFeatureState(
          { source: SOURCE_ID, id: selectedId.current },
          { selected: false }
        );
      }
      selectedId.current = id;
      map.current.setFeatureState(
        { source: SOURCE_ID, id },
        { selected: true }
      );
      onNeighborhoodClick(e.features[0].properties);
    }
  }, [containerRef, tooltipRef, onNeighborhoodClick]);

  // clear selection when popup closed
  useEffect(() => {
    if (!map.current) return;
    if (selectedNeighborhood === null && selectedId.current !== null) {
      map.current.setFeatureState(
        { source: SOURCE_ID, id: selectedId.current },
        { selected: false }
      );
      selectedId.current = null;
    }
  }, [selectedNeighborhood]);
}

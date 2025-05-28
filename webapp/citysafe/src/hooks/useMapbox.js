// src/hooks/useMapbox.js
import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import {
  MAP_STYLE, MAP_BOUNDS, START_VIEW,
  SOURCE_ID, GEOJSON_URL, LAYERS, MAPBOX_TOKEN
} from '../config/mapConfig';

mapboxgl.accessToken = MAPBOX_TOKEN;

export default function useMapbox({
  containerRef,
  tooltipRef,
  onNeighborhoodClick,
  selectedNeighborhood,
  nameToIdMap,
  searchName
}) {
  const map         = useRef(null);
  const hoveredFid  = useRef(null);
  const selectedFid = useRef(null);

  // 1) initialisation de la map et des handlers
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
      map.current.addLayer({ ...LAYERS.fill,    source: SOURCE_ID });
      map.current.addLayer({ ...LAYERS.outline, source: SOURCE_ID });
      map.current.addLayer({ ...LAYERS.label,   source: SOURCE_ID });

      map.current.on('mousemove', LAYERS.fill.id, onMouseMove);
      map.current.on('mouseleave', LAYERS.fill.id, onMouseLeave);
      map.current.on('click',      LAYERS.fill.id, onClickFeature);
    });

    function onMouseMove(e) {
      const f = e.features[0];
      if (!f) return;
      if (hoveredFid.current !== null) {
        map.current.setFeatureState(
          { source: SOURCE_ID, id: hoveredFid.current },
          { hover: false }
        );
      }
      hoveredFid.current = f.id;
      map.current.setFeatureState(
        { source: SOURCE_ID, id: f.id },
        { hover: true }
      );

      tooltipRef.current.style.display = 'block';
      tooltipRef.current.innerText     = f.properties.NTAName;
      tooltipRef.current.style.left    = `${e.point.x + 10}px`;
      tooltipRef.current.style.top     = `${e.point.y + 10}px`;
    }

    function onMouseLeave() {
      if (hoveredFid.current !== null) {
        map.current.setFeatureState(
          { source: SOURCE_ID, id: hoveredFid.current },
          { hover: false }
        );
      }
      hoveredFid.current = null;
      tooltipRef.current.style.display = 'none';
    }

    function onClickFeature(e) {
      const f = e.features[0];
      if (!f) return;

      // clear old selection
      if (selectedFid.current !== null) {
        map.current.setFeatureState(
          { source: SOURCE_ID, id: selectedFid.current },
          { selected: false }
        );
      }

      // set new selection
      selectedFid.current = f.id;
      map.current.setFeatureState(
        { source: SOURCE_ID, id: f.id },
        { selected: true }
      );

      // lookup dbId and open popup
      const name = f.properties.NTAName.trim();
      const dbId = nameToIdMap[name];
      if (!dbId) {
        console.warn(`No DB id for "${name}"`);
        return;
      }
      onNeighborhoodClick(dbId);
    }
  }, [
    containerRef,
    tooltipRef,
    onNeighborhoodClick,
    nameToIdMap
  ]);

  // 2) effet pour la SearchBar 🔍
  useEffect(() => {
    console.log('🔄 Search effect triggered:', searchName, 'map?', !!map.current);
    if (!map.current || !searchName) return;

    // utilise queryRenderedFeatures, pas querySourceFeatures
    const feats = map.current.queryRenderedFeatures({
      layers: [LAYERS.fill.id]
    });
    console.log('👀 rendered features count:', feats.length);

    const f = feats.find(feat =>
      feat.properties.NTAName.trim() === searchName
    );
    console.log('🔎 feature trouvée:', f);

    if (!f) {
      console.warn('Search: quartier non trouvé', searchName);
      return;
    }

    // clear old selection
    if (selectedFid.current !== null) {
      map.current.setFeatureState(
        { source: SOURCE_ID, id: selectedFid.current },
        { selected: false }
      );
    }

    // set new selection on the feature
    selectedFid.current = f.id;
    map.current.setFeatureState(
      { source: SOURCE_ID, id: f.id },
      { selected: true }
    );

    // open popup
    const dbId = nameToIdMap[searchName];
    onNeighborhoodClick(dbId);

  }, [searchName, nameToIdMap, onNeighborhoodClick]);

  // 3) clear highlight when popup closes
  useEffect(() => {
    if (!map.current || selectedNeighborhood !== null) return;
    if (selectedFid.current !== null) {
      map.current.setFeatureState(
        { source: SOURCE_ID, id: selectedFid.current },
        { selected: false }
      );
      selectedFid.current = null;
    }
  }, [selectedNeighborhood]);
}

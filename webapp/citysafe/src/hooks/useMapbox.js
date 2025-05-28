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

  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: containerRef.current,
      style:     MAP_STYLE,
      ...START_VIEW,
      maxBounds: MAP_BOUNDS
    });

    map.current.on('load', async () => {
      map.current.addSource(SOURCE_ID, { type: 'geojson', data: GEOJSON_URL });
      map.current.addLayer({ ...LAYERS.fill,    source: SOURCE_ID });
      map.current.addLayer({ ...LAYERS.outline, source: SOURCE_ID });
      map.current.addLayer({ ...LAYERS.label,   source: SOURCE_ID });

      const resp = await fetch('/api/complaints');
      const crimes = await resp.json();
      const crimeGeojson = {
        type: 'FeatureCollection',
        features: crimes
          .filter(c => c.latitude && c.longitude)
          .map(c => ({
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [c.longitude, c.latitude]
            },
            properties: {
              id: c.id,
              type: c.ofns_desc
            }
          }))
      };

      map.current.addSource('crimes', {
        type: 'geojson',
        data: crimeGeojson,
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50
      });

      map.current.addLayer({
        id: 'crime-heatmap',
        type: 'heatmap',
        source: 'crimes',
        maxzoom: 12,
        paint: {
          'heatmap-weight': ['interpolate', ['linear'], ['get', 'point_count'], 0, 0, 100, 1],
          'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 12, 3],
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0, 'rgba(33,102,172,0)',
            0.2, 'rgb(103,169,207)',
            0.4, 'rgb(209,229,240)',
            0.6, 'rgb(253,219,199)',
            0.8, 'rgb(239,138,98)',
            1, 'rgb(178,24,43)'
          ],
          'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 2, 12, 20],
          'heatmap-opacity': 0.6
        }
      });

      map.current.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'crimes',
        filter: ['has', 'point_count'],
        minzoom: 12,
        paint: {
          'circle-color': [
            'step',
            ['get', 'point_count'],
            '#51bbd6', 50,
            '#f1f075', 200,
            '#f28cb1'
          ],
          'circle-radius': [
            'step',
            ['get', 'point_count'],
            20, 50,
            30, 200,
            40
          ]
        }
      });

      map.current.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'crimes',
        filter: ['has', 'point_count'],
        minzoom: 12,
        layout: {
          'text-field': '{point_count_abbreviated}',
          'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
          'text-size': 12
        },
        paint: {
          'text-color': '#000'
        }
      });

      map.current.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: 'crimes',
        filter: ['!', ['has', 'point_count']],
        minzoom: 12,
        paint: {
          'circle-color': '#11b4da',
          'circle-radius': 4,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#fff'
        }
      });

      map.current.on('mousemove', LAYERS.fill.id, onMouseMove);
      map.current.on('mouseleave', LAYERS.fill.id, onMouseLeave);
      map.current.on('click',      LAYERS.fill.id, onClickFeature);
    });

    function onMouseMove(e) {
      const f = e.features[0];
      if (!f) return;
      if (hoveredFid.current !== null) {
        map.current.setFeatureState({ source: SOURCE_ID, id: hoveredFid.current }, { hover: false });
      }
      hoveredFid.current = f.id;
      map.current.setFeatureState({ source: SOURCE_ID, id: f.id }, { hover: true });
      tooltipRef.current.style.display = 'block';
      tooltipRef.current.innerText     = f.properties.NTAName;
      tooltipRef.current.style.left    = `${e.point.x + 10}px`;
      tooltipRef.current.style.top     = `${e.point.y + 10}px`;
    }

    function onMouseLeave() {
      if (hoveredFid.current !== null) {
        map.current.setFeatureState({ source: SOURCE_ID, id: hoveredFid.current }, { hover: false });
      }
      hoveredFid.current = null;
      tooltipRef.current.style.display = 'none';
    }

    function onClickFeature(e) {
      const f = e.features[0];
      if (!f) return;
      if (selectedFid.current !== null) {
        map.current.setFeatureState({ source: SOURCE_ID, id: selectedFid.current }, { selected: false });
      }
      selectedFid.current = f.id;
      map.current.setFeatureState({ source: SOURCE_ID, id: f.id }, { selected: true });
      const dbId = nameToIdMap[f.properties.NTAName.trim()];
      onNeighborhoodClick(dbId);
    }
  }, [containerRef, tooltipRef, onNeighborhoodClick, nameToIdMap]);

  useEffect(() => {
    if (!map.current || !searchName) return;
    const feats = map.current.queryRenderedFeatures({ layers: [LAYERS.fill.id] });
    const f = feats.find(feat => feat.properties.NTAName.trim() === searchName);
    if (!f) return;
    if (selectedFid.current !== null) {
      map.current.setFeatureState({ source: SOURCE_ID, id: selectedFid.current }, { selected: false });
    }
    selectedFid.current = f.id;
    map.current.setFeatureState({ source: SOURCE_ID, id: f.id }, { selected: true });
    onNeighborhoodClick(nameToIdMap[searchName]);
  }, [searchName, nameToIdMap, onNeighborhoodClick]);

  useEffect(() => {
    if (!map.current || selectedNeighborhood !== null) return;
    if (selectedFid.current !== null) {
      map.current.setFeatureState({ source: SOURCE_ID, id: selectedFid.current }, { selected: false });
      selectedFid.current = null;
    }
  }, [selectedNeighborhood]);
}

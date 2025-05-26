// src/components/MapView.jsx

import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import { MAPBOX_TOKEN } from '../config';
import '../styles/MapView.scss';

mapboxgl.accessToken = MAPBOX_TOKEN;

export default function MapView({ crimeData }) {
  const mapContainer = useRef(null);
  const map = useRef(null);

  useEffect(() => {
    if (map.current) return;

    let hoveredStateId = null;

    const nyBounds = [
      [-74.25909, 40.477399],
      [-73.700272, 40.917577]
    ];

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [-74.0060, 40.7128],
      zoom: 10,
      minZoom: 9,
      maxZoom: 15,
      maxBounds: nyBounds
    });

    map.current.on('load', () => {
      map.current.addSource('neighborhoods', {
        type: 'geojson',
        data: '/neighborhoods.geojson'
      });

      map.current.addLayer({
        id: 'neighborhoods-outline',
        type: 'line',
        source: 'neighborhoods',
        paint: {
          'line-color': '#007CBF',
          'line-width': 2
        }
      });

      map.current.addLayer({
        id: 'neighborhoods-fill',
        type: 'fill',
        source: 'neighborhoods',
        paint: {
          'fill-color': '#007CBF',
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.3,
            0.1 
          ]
        }
      });

      map.current.addLayer({
        id: 'neighborhoods-label',
        type: 'symbol',
        source: 'neighborhoods',
        minzoom: 12,
        layout: {
          'text-field': ['get', 'NTAName'],
          'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
          'text-size': 12,
          'text-allow-overlap': false
        },
        paint: {
          'text-color': '#777'
        }
      });

      map.current.on('mousemove', 'neighborhoods-fill', (e) => {
        if (!e.features.length) return;

        if (hoveredStateId !== null) {
          map.current.setFeatureState(
            { source: 'neighborhoods', id: hoveredStateId },
            { hover: false }
          );
        }

        hoveredStateId = e.features[0].id;
        map.current.setFeatureState(
          { source: 'neighborhoods', id: hoveredStateId },
          { hover: true }
        );
      });

      map.current.on('mouseleave', 'neighborhoods-fill', () => {
        if (hoveredStateId !== null) {
          map.current.setFeatureState(
            { source: 'neighborhoods', id: hoveredStateId },
            { hover: false }
          );
        }
        hoveredStateId = null;
      });
    });
  }, [crimeData]);

  return <div ref={mapContainer} className="map-container" />;
}

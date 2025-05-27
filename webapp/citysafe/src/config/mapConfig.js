export const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
export const MAP_STYLE = 'mapbox://styles/mapbox/light-v11';
export const MAP_BOUNDS = [
  [-74.25909, 40.477399],
  [-73.700272, 40.917577]
];
export const START_VIEW = { center: [-74.0060, 40.7128], zoom: 10, minZoom: 9, maxZoom: 15 };

export const SOURCE_ID       = 'neighborhoods';
export const GEOJSON_URL     = '/neighborhoods.geojson';

export const LAYERS = {
  fill: {
    id: 'neighborhoods-fill',
    type: 'fill',
    paint: {
      'fill-color': [
        'case',
        ['boolean', ['feature-state', 'selected'], false], '#005b99',
        ['boolean', ['feature-state', 'hover'],    false], '#00b0ff',
        '#007CBF'
      ],
      'fill-opacity': [
        'case',
        ['boolean', ['feature-state', 'selected'], false], 1,
        ['boolean', ['feature-state', 'hover'],    false], 0.3,
        0.1
      ]
    }
  },
  outline: {
    id: 'neighborhoods-outline',
    type: 'line',
    paint: {
      'line-color': '#007CBF',
      'line-width': 2
    }
  },
  label: {
    id: 'neighborhoods-label',
    type: 'symbol',
    minzoom: 12,
    layout: {
      'text-field': ['get', 'NTAName'],
      'text-font':  ['Open Sans Bold', 'Arial Unicode MS Bold'],
      'text-size':  12
    },
    paint: { 'text-color': '#333' }
  }
};

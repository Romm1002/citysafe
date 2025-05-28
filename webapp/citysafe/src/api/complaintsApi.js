import http from './http';

export function fetchCrimeTypeCounts(neighborhoodId) {
  return http.get('/complaints/type_counts', {
    params: { neighborhood_id: neighborhoodId }
  }).then(res => res.data);
}

export function fetchTopNeighborhoods(crimeType, limit = 5) {
  return http.get('/complaints/top_neighborhoods', {
    params: { crime_type: crimeType, limit }
  }).then(res => res.data);
}

export function fetchCrimeTypes() {
  return http.get('/complaints/types').then(res => res.data);
}

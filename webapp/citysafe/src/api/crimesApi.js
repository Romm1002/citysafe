import http from './http';

// GET  /api/crimes?borough=Brooklyn&type=THEFT
export function fetchCrimes(filters = {}) {
  return http.get('/crimes', { params: filters })
    .then(res => res.data);
}

// GET /api/neighborhoods
export function fetchNeighborhoods() {
  return http.get('/neighborhoods')
    .then(res => res.data);
}

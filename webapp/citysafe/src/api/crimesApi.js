import http from './http';

export function fetchCrimes(filters = {}) {
  return http.get('/crimes', { params: filters })
    .then(res => res.data);
}

export function fetchNeighborhoods() {
  return http.get('/neighborhoods')
    .then(res => res.data);
}

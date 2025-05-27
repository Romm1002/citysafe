import http from './http';

export function fetchNeighborhoods() {
  return http.get('/neighborhoods').then(res => res.data);
}

export function fetchNeighborhood(id) {
  return http.get(`/neighborhoods/${id}`).then(res => res.data);
}

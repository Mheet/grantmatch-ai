import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
});

// ── Organizations ───────────────────────────────────────────────────────────
export const orgApi = {
  create: (data) => api.post("/organizations", data).then((r) => r.data),
  list:   ()     => api.get("/organizations").then((r) => r.data),
  get:    (id)   => api.get(`/organizations/${id}`).then((r) => r.data),
};

// ── Grants ──────────────────────────────────────────────────────────────────
export const grantsApi = {
  list: () => api.get("/grants").then((r) => r.data),
};

// ── Matches ─────────────────────────────────────────────────────────────────
export const matchesApi = {
  generate: (orgId)  => api.post(`/matches/generate/${orgId}`).then((r) => r.data),
  list:     (orgId)  => api.get(`/matches/${orgId}`).then((r) => r.data),
};

// ── LOI ─────────────────────────────────────────────────────────────────────
export const loiApi = {
  generate: (matchId) => api.post(`/loi/generate/${matchId}`).then((r) => r.data),
};

export default api;

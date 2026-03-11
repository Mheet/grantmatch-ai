import axios from "axios";
import { supabase } from "./supabase";

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api",
  headers: { "Content-Type": "application/json" },
});

// ── Auth interceptor — attach Supabase Bearer token to every request ────────
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  if (data?.session?.access_token) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  return config;
});

// ── Organizations ───────────────────────────────────────────────────────────
export const orgApi = {
  create: (data) => api.post("/organizations", data).then((r) => r.data),
  list:   ()     => api.get("/organizations").then((r) => r.data),
  get:    (id)   => api.get(`/organizations/${id}`).then((r) => r.data),
  getMe:  ()     => api.get("/organizations/me").then((r) => r.data),
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

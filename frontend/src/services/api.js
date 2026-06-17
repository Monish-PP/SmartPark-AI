import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ── JWT Interceptor ───────────────────────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Auto Token Refresh ────────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, { refresh });
          localStorage.setItem("access_token", data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post("/auth/register/", data),
  login:    (data) => api.post("/auth/login/", data),
  profile:  ()     => api.get("/auth/profile/"),
  updateProfile: (data) => api.patch("/auth/profile/", data),
  vehicles: ()     => api.get("/auth/vehicles/"),
  addVehicle:    (data) => api.post("/auth/vehicles/", data),
  deleteVehicle: (id)   => api.delete(`/auth/vehicles/${id}/`),
};

// ── Parking ───────────────────────────────────────────────────────────────────
export const parkingAPI = {
  search: (params) => api.get("/parking/search/", { params }),
  getLots: ()      => api.get("/parking/"),
  getLot:  (id)    => api.get(`/parking/${id}/`),
  createLot: (data) => api.post("/parking/", data),
  updateLot: (id, data) => api.patch(`/parking/${id}/`, data),
  deleteLot: (id)       => api.delete(`/parking/${id}/`),
  getSlots:  (lotId)    => api.get(`/parking/${lotId}/slots/`),
  addSlot:   (lotId, data) => api.post(`/parking/${lotId}/slots/`, data),
  getOccupancy: (lotId) => api.get(`/parking/${lotId}/occupancy/`),
};

// ── Bookings ──────────────────────────────────────────────────────────────────
export const bookingAPI = {
  create:        (data) => api.post("/bookings/create/", data),
  list:          ()     => api.get("/bookings/"),
  get:           (id)   => api.get(`/bookings/${id}/`),
  entry:         (id)   => api.post(`/bookings/${id}/entry/`),
  exit:          (id)   => api.post(`/bookings/${id}/exit/`),
  cancel:        (id)   => api.post(`/bookings/${id}/cancel/`),
  verifyPayment: (data) => api.post("/bookings/verify-payment/", data),
  addReview:     (data) => api.post("/bookings/reviews/", data),
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsAPI = {
  ownerDashboard: (period = "week") => api.get("/analytics/owner/", { params: { period } }),
  adminAnalytics: () => api.get("/analytics/admin/"),
  heatmap:        (type = "occupancy") => api.get("/analytics/heatmap/", { params: { type } }),
  forecast:       (lotId, hours = 24) => api.get(`/analytics/forecast/${lotId}/`, { params: { hours } }),
};

// ── Occupancy (Edge AI) ──────────────────────────────────────────────────────────────────
export const occupancyAPI = {
  getForLot: (lotId) => api.get(`/occupancy/${lotId}/`),
  getAll:    ()       => api.get("/occupancy/all/"),
};

export default api;

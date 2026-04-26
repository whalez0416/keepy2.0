import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Site {
  id: number;
  site_name: string;
  hospital_name?: string;
  homepage_url: string;
  form_url?: string;
  check_interval_minutes: number;
  form_check_interval_minutes: number;
  expected_success_text?: string;
  name_selector?: string;
  phone_selector?: string;
  subject_selector?: string;
  message_selector?: string;
  password_selector?: string;
  password_value?: string;
  agreement_selector?: string;
  submit_selector?: string;
  extra_steps_json?: string;
  is_active: boolean;
  created_at?: string;
}

export interface SiteCheckLog {
  id: number;
  site_id: number;
  status: string;
  response_time: number;
  checked_at: string;
  error_message?: string;
  screenshot_path?: string;
}

export interface Alert {
  id: number;
  site_id: number;
  check_type: string;
  alert_level: string;
  message: string;
  sent_at?: string;
  resolved_at?: string;
  created_at: string;
}

export const sitesApi = {
  list: () => api.get<Site[]>('/sites/'),
  get: (id: number) => api.get<Site>(`/sites/${id}`),
  create: (data: Partial<Site>) => api.post<Site>('/sites/', data),
  update: (id: number, data: Partial<Site>) => api.patch<Site>(`/sites/${id}`, data),
  delete: (id: number) => api.delete(`/sites/${id}`),
  manualCheck: (siteId: number) => api.post(`/checks/manual/${siteId}`),
};

export const logsApi = {
  list: (siteId?: number) => api.get<SiteCheckLog[]>('/logs/', { params: { site_id: siteId } }),
};

export const alertsApi = {
  list: (limit: number = 100) => api.get<Alert[]>('/alerts/', { params: { limit } }),
};

export default api;

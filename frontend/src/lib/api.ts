import axios from 'axios';

const API_BASE_URL = '/api';

// Create instance with interceptor for JWT
export const authApiInstance = axios.create({
  baseURL: API_BASE_URL,
});

authApiInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('keepy_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface User {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
}

export interface FormConfig {
  id: number;
  site_id: number;
  name: string;
  form_url: string;
  check_interval_minutes: number;
  expected_success_text?: string;
  name_selector?: string;
  phone_selector?: string;
  subject_selector?: string;
  message_selector?: string;
  password_selector?: string;
  password_value?: string;
  agreement_selector?: string;
  submit_selector?: string;
  is_active: boolean;
}

export interface SpamConfig {
  id: number;
  site_id: number;
  board_url: string;
  admin_id?: string;
  admin_pw?: string;
  keywords?: string;
  is_active: boolean;
}

export interface Site {
  id: number;
  site_name: string;
  hospital_name?: string;
  homepage_url: string;
  check_interval_minutes: number;
  extra_steps_json?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  form_configs: FormConfig[];
  spam_configs: SpamConfig[];
}

export interface SiteCheckLog {
  id: number;
  site_id: number;
  check_type: string;
  status: string;
  response_time: number;
  fail_reason?: string;
  raw_result?: string;
  screenshot_path?: string;
  checked_at: string;
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

export interface SpamPost {
  title: string;
  url?: string;
  author?: string;
  content_snippet?: string;
  method: 'keyword' | 'gemini_ai';
  confidence: number;
  reason: string;
}

export interface SpamScanResult {
  total_posts: number;
  spam_detected: number;
  spam_posts: SpamPost[];
  classification_method: string;
  duration_seconds: number;
}

export const authApi = {
  login: (email: string, password: string) => 
    axios.post(`${API_BASE_URL}/auth/login`, new URLSearchParams({ username: email, password })),
  register: (data: any) => 
    axios.post(`${API_BASE_URL}/auth/register`, data),
  getMe: () => 
    authApiInstance.get('/auth/me'),
};

export const sitesApi = {
  list: () => authApiInstance.get<Site[]>('/sites/'),
  get: (id: number) => authApiInstance.get<Site>(`/sites/${id}`),
  create: (data: any) => authApiInstance.post<Site>('/sites/', data),
  update: (id: number, data: any) => authApiInstance.patch<Site>(`/sites/${id}`, data),
  delete: (id: number) => authApiInstance.delete(`/sites/${id}`),
};

export const logsApi = {
  list: (params?: any) => authApiInstance.get<SiteCheckLog[]>('/logs/', { params }),
  getBySite: (siteId: number) => authApiInstance.get<SiteCheckLog[]>(`/logs/site/${siteId}`),
};

export const alertsApi = {
  list: () => authApiInstance.get<Alert[]>('/alerts/'),
};

export const spamApi = {
  getConfigs: (siteId: number) => authApiInstance.get<SpamConfig[]>(`/spam/config/site/${siteId}`),
  createConfig: (data: any) => authApiInstance.post<SpamConfig>('/spam/config/', data),
  deleteConfig: (id: number) => authApiInstance.delete(`/spam/config/${id}`),
  runConfig: (id: number) => authApiInstance.post<SpamScanResult>(`/spam/scan/${id}`),
};

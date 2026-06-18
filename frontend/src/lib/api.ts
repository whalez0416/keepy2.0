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

authApiInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('keepy_token');
      localStorage.removeItem('keepy_user');
      window.location.href = '/app/login';
    }
    return Promise.reject(error);
  }
);

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
  password_value?: string; // 쓰기 전용: 응답에는 안 옴. 빈 값으로 저장하면 기존 비번 유지
  has_password?: boolean;  // 비밀번호 저장 여부(응답에서 제공)
  agreement_selector?: string;
  submit_selector?: string;
  is_active: boolean;
}

export interface SpamConfig {
  id: number;
  site_id: number;
  board_url: string;
  admin_id?: string;
  admin_pw?: string;      // 쓰기 전용: 응답에는 안 옴. 빈 값으로 저장하면 기존 비번 유지
  has_admin_pw?: boolean; // 비밀번호 저장 여부(응답에서 제공)
  keywords?: string;
  is_active: boolean;
}

export interface Site {
  id: number;
  org_id: number;
  site_name: string;
  hospital_name?: string;
  homepage_url: string;
  check_interval_minutes: number;
  extra_steps_json?: string;
  baseline_screenshot_path?: string;
  emergency_mode_active: boolean;
  emergency_message?: string;
  admin_path?: string;
  whitelisted_ips?: string;
  expected_phone?: string;
  expected_kakao_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_check_status?: string;
  last_check_at?: string;
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
  method: 'keyword' | 'openai_ai';
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

export interface Organization {
  id: number;
  name: string;
  slug: string;
  logo_url?: string;
  billing_email?: string;
  notify_emails?: string;
  notify_phones?: string;
  is_active: boolean;
}

export const authApi = {
  login: (email: string, password: string) => 
    axios.post(`${API_BASE_URL}/auth/login`, new URLSearchParams({ username: email, password })),
  register: (data: any) => 
    axios.post(`${API_BASE_URL}/auth/register`, data),
  getMe: () =>
    authApiInstance.get('/auth/me'),
  createHospitalAdmin: (data: any) =>
    authApiInstance.post('/auth/create-hospital-admin', data),
  changePassword: (current_password: string, new_password: string) =>
    authApiInstance.post('/auth/change-password', { current_password, new_password }),
};

export const organizationsApi = {
  list: () => authApiInstance.get<Organization[]>('/organizations/'),
  get: (id: number) => authApiInstance.get<Organization>(`/organizations/${id}`),
  create: (data: any) => authApiInstance.post<Organization>('/organizations/', data),
  update: (id: number, data: Partial<Organization>) =>
    authApiInstance.patch<Organization>(`/organizations/${id}`, data),
};

export const sitesApi = {
  list: () => authApiInstance.get<Site[]>('/sites/'),
  get: (id: number) => authApiInstance.get<Site>(`/sites/${id}`),
  create: (data: any) => authApiInstance.post<Site>('/sites/', data),
  update: (id: number, data: any) => authApiInstance.patch<Site>(`/sites/${id}`, data),
  delete: (id: number) => authApiInstance.delete(`/sites/${id}`),
  manualCheck: (id: number) => authApiInstance.post(`/checks/run/${id}`),
};

export const logsApi = {
  list: (params?: any) => authApiInstance.get<SiteCheckLog[]>('/logs/', { params }),
  getBySite: (siteId: number) => authApiInstance.get<SiteCheckLog[]>(`/logs/site/${siteId}`),
};

export const alertsApi = {
  list: () => authApiInstance.get<Alert[]>('/alerts/'),
};

export const spamApi = {
  getConfigs: (siteId: number) => authApiInstance.get<SpamConfig[]>(`/spam/configs/${siteId}`),
  createConfig: (data: any) => authApiInstance.post<SpamConfig>('/spam/configs', data),
  deleteConfig: (id: number) => authApiInstance.delete(`/spam/configs/${id}`),
  runConfig: (id: number) => authApiInstance.post<SpamScanResult>(`/spam/configs/${id}/run`),
};

export const leadsApi = {
  list: () => authApiInstance.get('/leads/'),
  updateStatus: (id: number, status: string) => authApiInstance.patch(`/leads/${id}/status`, { status }),
};

export interface DiscoveredForm {
  url: string;
  link_text: string;
  confidence: number;
  selector_count: number;
  selectors: {
    name_selector?: string;
    phone_selector?: string;
    subject_selector?: string;
    message_selector?: string;
    agreement_selector?: string;
    submit_selector?: string;
  };
}

export interface DiscoveryResult {
  success: boolean;
  homepage_url: string;
  discovered_forms: DiscoveredForm[];
  error?: string;
}

export const discoveryApi = {
  discover: (homepageUrl: string) => 
    authApiInstance.post<DiscoveryResult>('/discovery/discover', { homepage_url: homepageUrl }),
};

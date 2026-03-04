import axios from 'axios';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';
import { showErrorToast, getErrorMessage } from './toast';

// API URL from environment — set EXPO_PUBLIC_API_URL in apps/mobile/.env
// Fallback: Android emulator uses 10.0.2.2, iOS/web use localhost
const API_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000');

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ────────────────────────────────────────────────────────────
// Request interceptor — inject JWT token
// ────────────────────────────────────────────────────────────
api.interceptors.request.use(
  async (config) => {
    try {
      let token;
      if (Platform.OS === 'web') {
        token = localStorage.getItem('accessToken');
      } else {
        token = await SecureStore.getItemAsync('accessToken');
      }

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error reading token', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authEmitter = {
  listeners: [] as (() => void)[],
  subscribe(listener: () => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  },
  emit() {
    this.listeners.forEach((listener) => listener());
  },
};

let isRefreshing = false;
let failedQueue: { resolve: (value?: unknown) => void; reject: (reason?: any) => void }[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// ────────────────────────────────────────────────────────────
// Response interceptor — token refresh + S8-02: error toasts
// ────────────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // S8-02: Show toast for non-401 errors (401 is handled by refresh logic)
    if (error.response?.status !== 401 || originalRequest._retry) {
      // Don't toast for refresh token requests or already-retried requests
      if (!originalRequest._isRefreshRequest) {
        showErrorToast(getErrorMessage(error));
      }
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        let refreshToken;
        if (Platform.OS === 'web') {
          refreshToken = localStorage.getItem('refreshToken');
        } else {
          refreshToken = await SecureStore.getItemAsync('refreshToken');
        }

        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const refreshAxios = axios.create({ baseURL: API_URL });
        const { data } = await refreshAxios.post('/api/auth/token/refresh/', {
          refresh: refreshToken,
        });

        const newAccessToken = data.access;
        if (Platform.OS === 'web') {
          localStorage.setItem('accessToken', newAccessToken);
          if (data.refresh) localStorage.setItem('refreshToken', data.refresh);
        } else {
          await SecureStore.setItemAsync('accessToken', newAccessToken);
          if (data.refresh) await SecureStore.setItemAsync('refreshToken', data.refresh);
        }

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        processQueue(null, newAccessToken);

        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);

        await logout();

        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ────────────────────────────────────────────────────────────
// Types
// ────────────────────────────────────────────────────────────
export interface Badge {
  id: string;
  name: string;
  icon_url: string;
  is_owned: boolean;
}

export interface UserStats {
  global_score: number;
  win_rate: number;
  roi: number;
  badges: Badge[];
}

export interface UserProfile {
  id: string;
  username: string;
  avatar_url?: string;
  bio?: string;
  subscription_price?: string;
}

export interface TicketUser {
  username: string;
  avatar_url?: string;
}

export interface Ticket {
  id: string;
  image: string;
  total_odds: number;
  stake: number;
  potential_gain: number;
  status: 'won' | 'lost' | 'pending';
  created_at: string;
  user: TicketUser;
}

export interface DashboardData {
  active_subscribers: number;
  total_subscribers_ever: number;
  monthly_revenue_estimate: number;
  subscription_price: string;
  recent_subscriptions: Array<{
    follower_username: string;
    status: string;
    created_at: string;
  }>;
}

// ────────────────────────────────────────────────────────────
// Auth
// ────────────────────────────────────────────────────────────
export const logout = async () => {
  if (Platform.OS === 'web') {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  } else {
    await SecureStore.deleteItemAsync('accessToken');
    await SecureStore.deleteItemAsync('refreshToken');
  }
  authEmitter.emit();
  if (router) {
    router.replace('/login');
  }
};

// ────────────────────────────────────────────────────────────
// API Functions
// ────────────────────────────────────────────────────────────
export const getUserStats = async (): Promise<UserStats> => {
  const response = await api.get('/api/me/stats/');
  return response.data;
};

export const getUserProfile = async (): Promise<UserProfile> => {
  const response = await api.get('/api/me/');
  return response.data;
};

export const register = async (data: Record<string, any>) => {
  const response = await api.post('/api/auth/register/', data);
  return response.data;
};

export const uploadTicket = async (imageUri: string) => {
  const formData = new FormData();
  const filename = imageUri.split('/').pop() || 'ticket.jpg';
  const match = /\.(\w+)$/.exec(filename);
  const type = match ? `image/${match[1]}` : `image`;

  // @ts-ignore: React Native FormData expects an object with uri, name, type
  formData.append('image', { uri: imageUri, name: filename, type });

  const response = await api.post('/api/tickets/upload/', formData, {
    headers: { 'Content-Type': undefined },
  });
  return response.data;
};

export const getTicketStatus = async (urlOrId: string) => {
  const url = urlOrId.startsWith('http') ? urlOrId : `/api/tickets/${urlOrId}/`;
  const response = await api.get(url);
  return response.data;
};

export const getTickets = async (page: number = 1): Promise<{ results: Ticket[]; next: string | null; previous: string | null; count: number }> => {
  const response = await api.get(`/api/tickets/list/?page=${page}`);
  return response.data;
};

export const fetchMyProfile = async () => {
  const { data } = await api.get('/api/me/');
  return data;
};

export const createBet = async (formData: FormData) => {
  const { data } = await api.post('/api/bets/', formData, {
    headers: { 'Content-Type': undefined },
  });
  return data;
};

export const fetchBets = async () => {
  const { data } = await api.get('/api/bets/');
  return data;
};

export const uploadTicketImage = async (formData: FormData) => {
  const { data } = await api.post('/api/tickets/upload/', formData, {
    headers: { 'Content-Type': undefined },
  });
  return data;
};

export const pollTicketStatus = async (ticketId: string) => {
  const { data } = await api.get(`/api/tickets/${ticketId}/status/`);
  return data;
};

export const createConnectedAccount = async () => {
  const { data } = await api.post('/api/connect/create-account/');
  return data;
};

export const getOnboardingLink = async () => {
  const { data } = await api.get('/api/connect/onboarding-link/');
  return data;
};

export const createSubscriptionCheckout = async (tipsterId: string, successUrl: string, cancelUrl: string) => {
  const { data } = await api.post('/api/subscriptions/subscribe/', {
    tipster_id: tipsterId,
    success_url: successUrl,
    cancel_url: cancelUrl,
  });
  return data;
};

export const getMySubscriptions = async () => {
  const { data } = await api.get('/api/me/subscriptions/');
  return data;
};

export const getDashboard = async (): Promise<DashboardData> => {
  const { data } = await api.get('/api/me/dashboard/');
  return data;
};

export const settleBet = async (betId: string, outcome: 'WON' | 'LOST' | 'VOID') => {
  const { data } = await api.post(`/api/bets/${betId}/settle/`, { outcome });
  return data;
};

export const cancelSubscription = async (subscriptionId: string) => {
  const { data } = await api.post('/api/subscriptions/cancel/', {
    subscription_id: subscriptionId,
  });
  return data;
};

export const requestPasswordReset = async (email: string) => {
  const { data } = await api.post('/api/auth/password-reset/', { email });
  return data;
};

// ────────────────────────────────────────────────────────────
// S8-01: Profile Update
// ────────────────────────────────────────────────────────────
export const updateProfile = async (data: { bio?: string; avatar?: any }) => {
  const formData = new FormData();

  if (data.bio !== undefined) {
    formData.append('bio', data.bio);
  }

  if (data.avatar) {
    const filename = data.avatar.uri.split('/').pop() || 'avatar.jpg';
    const matchExt = /\.(\w+)$/.exec(filename);
    const type = matchExt ? `image/${matchExt[1]}` : 'image/jpeg';

    // @ts-ignore
    formData.append('avatar', {
      uri: data.avatar.uri,
      name: filename,
      type,
    });
  }

  const response = await api.put('/api/me/profile/', formData, {
    headers: { 'Content-Type': undefined },
  });
  return response.data;
};

// ────────────────────────────────────────────────────────────
// S8-05: Update Subscription Price
// ────────────────────────────────────────────────────────────
export const updateSubscriptionPrice = async (price: string) => {
  const { data } = await api.post('/api/me/dashboard/', {
    subscription_price: price,
  });
  return data;
};

// ────────────────────────────────────────────────────────────
// Sprint 11: Password Reset Confirm
// ────────────────────────────────────────────────────────────
export const confirmPasswordReset = async (uid: string, token: string, newPassword: string) => {
  const { data } = await api.post('/api/auth/password-reset/confirm/', {
    uid,
    token,
    new_password: newPassword,
  });
  return data;
};

// ────────────────────────────────────────────────────────────
// Sprint 11: Report content/user
// ────────────────────────────────────────────────────────────
export const submitReport = async (params: {
  reported_user?: number;
  reported_bet?: string;
  reported_comment?: number;
  reason: 'SPAM' | 'INAPPROPRIATE' | 'FRAUD' | 'HARASSMENT' | 'OTHER';
  details?: string;
}) => {
  const { data } = await api.post('/api/social/reports/', params);
  return data;
};

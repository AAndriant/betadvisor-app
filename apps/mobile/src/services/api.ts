import axios from 'axios';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';

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

// Add a request interceptor to inject the token
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

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

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

        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

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
}

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

  // Infer the type of the image
  const match = /\.(\w+)$/.exec(filename);
  const type = match ? `image/${match[1]}` : `image`;

  // @ts-ignore: React Native FormData expects an object with uri, name, type
  formData.append('image', { uri: imageUri, name: filename, type });

  const response = await api.post('/api/tickets/upload/', formData, {
    headers: {
      // Explicitly undefined to let the browser/engine set the Content-Type with boundary
      'Content-Type': undefined,
    },
  });
  return response.data;
};

export const getTicketStatus = async (urlOrId: string) => {
  // If it's a full URL (starts with http), use it directly.
  // Otherwise, assume it's an ID and construct the URL.
  const url = urlOrId.startsWith('http') ? urlOrId : `/api/tickets/${urlOrId}/`;
  const response = await api.get(url);
  return response.data;
};

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

export const getTickets = async (page: number = 1): Promise<{ results: Ticket[]; next: string | null; previous: string | null; count: number }> => {
  const response = await api.get(`/api/tickets/list/?page=${page}`);
  return response.data;
};

export const fetchMyProfile = async () => {
  try {
    const { data } = await api.get('/api/me/');
    return data;
  } catch (error) {
    console.error("Erreur fetchMyProfile:", error);
    throw error;
  }
};

export const createBet = async (formData: FormData) => {
  try {
    // ✅ FIX: Ne PAS mettre le Content-Type explicitement pour FormData
    // Axios/Browser va automatiquement ajouter le boundary nécessaire
    const { data } = await api.post('/api/bets/', formData, {
      headers: {
        'Content-Type': undefined,
      },
    });
    return data;
  } catch (error) {
    console.error("Erreur createBet:", error);
    throw error;
  }
};

export const fetchBets = async () => {
  const { data } = await api.get('/api/bets/');
  return data;
};

// Upload l'image et récupère l'URL de suivi (legacy — utiliser uploadTicket() si possible)
export const uploadTicketImage = async (formData: FormData) => {
  // ✅ FIX: ajout du préfixe /api/ manquant + suppression Content-Type explicite
  const { data } = await api.post('/api/tickets/upload/', formData, {
    headers: { 'Content-Type': undefined },
  });
  return data; // Attend { ticket_id: '...', status_url: '...' }
};

// Vérifie le statut
export const pollTicketStatus = async (ticketId: string) => {
  // ✅ FIX: ajout du préfixe /api/ manquant
  const { data } = await api.get(`/api/tickets/${ticketId}/status/`);
  return data; // Attend { status: 'PROCESSING' | 'VALIDATED', ocr_data: {...} }
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

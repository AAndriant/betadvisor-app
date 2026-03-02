import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
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

let isRefreshing = false;
let failedQueue: { resolve: (value?: unknown) => void; reject: (reason?: any) => void }[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
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
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = 'Bearer ' + token;
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

        // Use a clean axios instance to avoid interceptor loops
        const refreshResponse = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const newAccessToken = refreshResponse.data.access;
        // Optionally update refresh token if returned
        const newRefreshToken = refreshResponse.data.refresh;

        if (Platform.OS === 'web') {
          localStorage.setItem('accessToken', newAccessToken);
          if (newRefreshToken) localStorage.setItem('refreshToken', newRefreshToken);
        } else {
          await SecureStore.setItemAsync('accessToken', newAccessToken);
          if (newRefreshToken) await SecureStore.setItemAsync('refreshToken', newRefreshToken);
        }

        api.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);

        // Clear tokens and redirect to login
        if (Platform.OS === 'web') {
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
        } else {
          await SecureStore.deleteItemAsync('accessToken');
          await SecureStore.deleteItemAsync('refreshToken');
        }

        router.replace('/login');
        return Promise.reject(refreshError);
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

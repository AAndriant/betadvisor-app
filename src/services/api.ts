import axios from 'axios';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// Define the API URL based on the platform
const API_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

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
  const response = await api.get('/api/users/me/stats/');
  return response.data;
};

export const getUserProfile = async (): Promise<UserProfile> => {
  const response = await api.get('/api/users/me/');
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
    const { data } = await api.get('/api/users/me/');
    return data;
  } catch (error) {
    console.error("Erreur fetchMyProfile:", error);
    throw error;
  }
};

export const createBet = async (formData: FormData) => {
  try {
    const { data } = await api.post('/api/bets/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
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

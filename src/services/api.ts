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
      const token = await SecureStore.getItemAsync('accessToken');
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

export const uploadTicket = async (formData: FormData) => {
  const response = await api.post('/api/tickets/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

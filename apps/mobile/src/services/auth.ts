import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';

// Simple event emitter to decouple AuthContext and API interceptors
type Listener = () => void;
let logoutListeners: Listener[] = [];

export const onForceLogout = (listener: Listener) => {
  logoutListeners.push(listener);
  return () => {
    logoutListeners = logoutListeners.filter(l => l !== listener);
  };
};

export const performLogout = async () => {
  try {
    // Notify AuthContext synchronously to clear its state
    // preventing infinite redirect loops
    logoutListeners.forEach(listener => listener());

    if (Platform.OS === 'web') {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    } else {
      await SecureStore.deleteItemAsync('accessToken');
      await SecureStore.deleteItemAsync('refreshToken');
    }

    // Force redirect to login page
    if (router && router.replace) {
      router.replace('/login');
    }
  } catch (error) {
    console.error('Error during logout:', error);
  }
};

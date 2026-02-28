import React, { createContext, useContext, useState, useEffect } from 'react';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { api } from '../services/api';

interface User {
  username: string;
  // Add other user fields if needed
}

interface AuthContextProps {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextProps>({} as AuthContextProps);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadToken = async () => {
      try {
        let token;
        if (Platform.OS === 'web') {
          token = localStorage.getItem('accessToken');
        } else {
          token = await SecureStore.getItemAsync('accessToken');
        }

        if (token) {
          setAccessToken(token);
          // Optionally here we could fetch user profile if the token is valid
          // For now we assume if token exists we are partially logged in
          // (though we don't have user details without a profile endpoint call)
          // To be safe, we might want to decode the token or fetch /me.
          // But based on requirements, we just persist state.
          // Let's at least set a dummy user or just the token.
          // The prompt says "AuthContext qui stocke : user, accessToken, isLoading".
          // I will assume for now we don't have a user endpoint, but I will try to infer username if possible or just leave user null until refreshed.
          // Actually, let's keep it simple: if token exists, we set it.
        }
      } catch (e) {
        console.error("Failed to load token", e);
      } finally {
        setIsLoading(false);
      }
    };
    loadToken();
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await api.post('/api/auth/token/', { username, password });
      const { access, refresh } = response.data;

      if (Platform.OS === 'web') {
        localStorage.setItem('accessToken', access);
        if (refresh) localStorage.setItem('refreshToken', refresh);
      } else {
        await SecureStore.setItemAsync('accessToken', access);
        if (refresh) {
            await SecureStore.setItemAsync('refreshToken', refresh);
        }
      }

      setAccessToken(access);
      setUser({ username }); // We assume success implies the user is who they say they are
    } catch (error) {
      console.error("Login failed", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      if (Platform.OS === 'web') {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
      } else {
        await SecureStore.deleteItemAsync('accessToken');
        await SecureStore.deleteItemAsync('refreshToken');
      }
      setAccessToken(null);
      setUser(null);
    } catch (error) {
        console.error("Logout failed", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, accessToken, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

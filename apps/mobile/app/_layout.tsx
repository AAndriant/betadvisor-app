import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { View } from 'react-native';
import Toast from 'react-native-toast-message';
import "../global.css";
import { AuthProvider } from '../src/context/AuthContext';
import { registerForPushNotifications } from '../src/services/notifications';

const queryClient = new QueryClient();

export default function RootLayout() {
    useEffect(() => {
        // S8-03: Register for push notifications on app launch
        registerForPushNotifications();
    }, []);

    return (
        <QueryClientProvider client={queryClient}>
            <SafeAreaProvider>
                <AuthProvider>
                    <View className="flex-1 bg-slate-950">
                        <Stack screenOptions={{ headerShown: false }}>
                            <Stack.Screen name="(tabs)" />
                        </Stack>
                    </View>
                    {/* S8-02: Global Toast component */}
                    <Toast />
                </AuthProvider>
            </SafeAreaProvider>
        </QueryClientProvider>
    );
}

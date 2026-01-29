import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { View } from 'react-native';
import "../global.css";
import { AuthProvider } from '../src/context/AuthContext';

const queryClient = new QueryClient();

export default function RootLayout() {
    return (
        <QueryClientProvider client={queryClient}>
            <SafeAreaProvider>
                <AuthProvider>
                    <View className="flex-1 bg-slate-950">
                        <Stack screenOptions={{ headerShown: false }}>
                            <Stack.Screen name="(tabs)" />
                        </Stack>
                    </View>
                </AuthProvider>
            </SafeAreaProvider>
        </QueryClientProvider>
    );
}

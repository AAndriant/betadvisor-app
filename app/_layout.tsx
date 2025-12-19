import { Slot } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import "../global.css";
import { AuthProvider } from '../src/context/AuthContext';

const queryClient = new QueryClient();

export default function RootLayout() {
    return (
        <QueryClientProvider client={queryClient}>
            <SafeAreaProvider>
                <AuthProvider>
                    <Slot />
                </AuthProvider>
            </SafeAreaProvider>
        </QueryClientProvider>
    );
}

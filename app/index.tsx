import { View, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useEffect } from 'react';
import { useAuth } from '../src/context/AuthContext';

export default function Index() {
    const { accessToken, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (isLoading) return;

        if (accessToken) {
            // Redirect to the home tab
            router.replace('/(tabs)/feed');
        } else {
            router.replace('/login');
        }
    }, [accessToken, isLoading, router]);

    return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <ActivityIndicator size="large" color="#0000ff" />
        </View>
    );
}

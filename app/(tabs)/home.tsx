import { View, Text, TouchableOpacity } from 'react-native';
import { Link } from 'expo-router';
import { api } from '../../src/services/api';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../src/context/AuthContext';

export default function TabIndex() {
    const { logout } = useAuth();
    const { data, error, isLoading, refetch } = useQuery({
        queryKey: ['smokeTest'],
        queryFn: async () => {
            const response = await api.get('/admin/');
            return response.data;
        },
        enabled: false,
    });

    const handleTestBackend = () => {
        refetch();
    };

    return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'white' }}>
            <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 16 }}>Dashboard (Protected)</Text>

            <TouchableOpacity
                onPress={handleTestBackend}
                style={{ backgroundColor: '#3b82f6', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 }}
            >
                <Text style={{ color: 'white', fontWeight: '600' }}>Test Backend</Text>
            </TouchableOpacity>

            <Link href="/create-ticket" asChild>
                <TouchableOpacity style={{ marginTop: 20, backgroundColor: '#10b981', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 }}>
                    <Text style={{ color: 'white', fontWeight: '600' }}>Nouveau Ticket</Text>
                </TouchableOpacity>
            </Link>

            <TouchableOpacity
                onPress={logout}
                style={{ marginTop: 20, backgroundColor: '#ef4444', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 }}
            >
                <Text style={{ color: 'white', fontWeight: '600' }}>Se déconnecter</Text>
            </TouchableOpacity>

            {isLoading && <Text style={{ marginTop: 16, color: '#6b7280' }}>Loading...</Text>}
            {error && <Text style={{ marginTop: 16, color: '#ef4444' }}>Error: {(error as Error).message}</Text>}
            {data && (
                <View style={{ marginTop: 16, padding: 16, backgroundColor: '#f3f4f6', borderRadius: 4 }}>
                    <Text style={{ color: '#16a34a' }}>Success!</Text>
                    <Text>{JSON.stringify(data, null, 2)}</Text>
                </View>
            )}
        </View>
    );
}

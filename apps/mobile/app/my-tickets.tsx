import React from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, Image, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Camera } from 'lucide-react-native';
import { getTickets } from '../src/services/api';

interface TicketItem {
    id: string;
    image: string;
    status: string;
    created: string;
    selections?: Array<{ match: string; odds: number }>;
}

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
    PENDING_OCR: { label: 'En attente', bg: 'bg-amber-500/20', text: 'text-amber-500' },
    PROCESSING: { label: 'Traitement', bg: 'bg-blue-500/20', text: 'text-blue-500' },
    VALIDATED: { label: 'Validé', bg: 'bg-emerald-500/20', text: 'text-emerald-500' },
    REVIEW_NEEDED: { label: 'À vérifier', bg: 'bg-yellow-500/20', text: 'text-yellow-500' },
    REJECTED: { label: 'Rejeté', bg: 'bg-red-500/20', text: 'text-red-500' },
};

function formatDate(dateStr: string): string {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 60) return `il y a ${minutes}min`;
    if (hours < 24) return `il y a ${hours}h`;
    if (days < 7) return `il y a ${days}j`;
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

export default function MyTicketsScreen() {
    const router = useRouter();

    const { data, isLoading, refetch } = useQuery({
        queryKey: ['myTickets'],
        queryFn: () => getTickets(1),
    });

    const tickets: TicketItem[] = (data?.results as any[]) || [];

    const renderItem = ({ item }: { item: TicketItem }) => {
        const statusConfig = STATUS_CONFIG[item.status] || STATUS_CONFIG.PENDING_OCR;

        return (
            <View className="bg-slate-900 border border-slate-800 rounded-xl p-3 mx-4 mb-3 flex-row">
                {/* Thumbnail */}
                {item.image ? (
                    <Image
                        source={{ uri: item.image }}
                        className="w-16 h-16 rounded-lg bg-slate-800 mr-3"
                        resizeMode="cover"
                    />
                ) : (
                    <View className="w-16 h-16 rounded-lg bg-slate-800 mr-3 items-center justify-center">
                        <Camera size={24} color="#475569" />
                    </View>
                )}

                {/* Content */}
                <View className="flex-1 justify-center">
                    <View className="flex-row items-center mb-1">
                        <View className={`px-2 py-0.5 rounded-full ${statusConfig.bg}`}>
                            <Text className={`text-xs font-bold ${statusConfig.text}`}>
                                {statusConfig.label}
                            </Text>
                        </View>
                    </View>

                    <Text className="text-slate-400 text-sm">
                        {formatDate(item.created)}
                    </Text>

                    {item.selections && item.selections.length > 0 && (
                        <Text className="text-slate-500 text-xs mt-1">
                            {item.selections.length} sélection{item.selections.length > 1 ? 's' : ''} détectée{item.selections.length > 1 ? 's' : ''}
                        </Text>
                    )}
                </View>
            </View>
        );
    };

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            {/* Header */}
            <View className="flex-row items-center px-4 py-3 border-b border-slate-800">
                <TouchableOpacity onPress={() => router.back()} className="mr-3 p-1">
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>
                <Text className="text-white font-bold text-xl">Mes Tickets</Text>
            </View>

            {isLoading ? (
                <View className="flex-1 justify-center items-center">
                    <ActivityIndicator size="large" color="#10b981" />
                </View>
            ) : (
                <FlatList
                    data={tickets}
                    keyExtractor={(item) => item.id}
                    renderItem={renderItem}
                    contentContainerStyle={{ paddingTop: 16, paddingBottom: 100 }}
                    refreshControl={
                        <RefreshControl
                            refreshing={isLoading}
                            onRefresh={() => refetch()}
                            tintColor="#10b981"
                        />
                    }
                    ListEmptyComponent={
                        <View className="flex-1 items-center justify-center py-20 px-8">
                            <Camera size={48} color="#475569" />
                            <Text className="text-slate-400 text-center mt-4 text-lg font-medium">
                                Aucun ticket uploadé
                            </Text>
                            <Text className="text-slate-500 text-center mt-2 text-sm">
                                Utilisez l'écran OCR pour scanner vos paris.
                            </Text>
                        </View>
                    }
                />
            )}
        </SafeAreaView>
    );
}

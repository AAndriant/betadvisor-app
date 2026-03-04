import React from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, Alert, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, CreditCard, Calendar, User } from 'lucide-react-native';
import { getMySubscriptions, cancelSubscription } from '../src/services/api';
import { showSuccessToast } from '../src/services/toast';

interface Subscription {
    id: string;
    tipster: { id: string; username: string } | string;
    tipster_username?: string;
    stripe_subscription_id: string;
    status: string;
    current_period_end: string;
    created_at: string;
}

function getTipsterName(sub: Subscription): string {
    if (typeof sub.tipster === 'object' && sub.tipster !== null) {
        return sub.tipster.username;
    }
    return sub.tipster_username || 'Tipster';
}

export default function MySubscriptionsScreen() {
    const router = useRouter();
    const queryClient = useQueryClient();

    const { data, isLoading, refetch } = useQuery({
        queryKey: ['mySubscriptions'],
        queryFn: getMySubscriptions,
    });

    const subscriptions: Subscription[] = Array.isArray(data) ? data : data?.results || [];

    const handleCancel = (sub: Subscription) => {
        Alert.alert(
            'Annuler l\'abonnement',
            `Voulez-vous vraiment annuler votre abonnement à ${getTipsterName(sub)} ?`,
            [
                { text: 'Non', style: 'cancel' },
                {
                    text: 'Oui, annuler',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await cancelSubscription(sub.id);
                            showSuccessToast('Abonnement annulé');
                            queryClient.invalidateQueries({ queryKey: ['mySubscriptions'] });
                        } catch {
                            // Error toast is handled by interceptor
                        }
                    },
                },
            ]
        );
    };

    const formatDate = (dateStr: string) => {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
    };

    const renderItem = ({ item }: { item: Subscription }) => (
        <View className="bg-slate-900 border border-slate-800 rounded-xl p-4 mx-4 mb-3">
            <View className="flex-row items-center mb-3">
                <View className="bg-slate-800 w-10 h-10 rounded-full items-center justify-center mr-3">
                    <User size={20} color="#10b981" />
                </View>
                <View className="flex-1">
                    <Text className="text-white font-bold text-lg">{getTipsterName(item)}</Text>
                    <View className="flex-row items-center mt-1">
                        <View className={`px-2 py-0.5 rounded-full ${item.status === 'active' ? 'bg-emerald-500/20' : 'bg-slate-700'}`}>
                            <Text className={`text-xs font-bold ${item.status === 'active' ? 'text-emerald-500' : 'text-slate-400'}`}>
                                {item.status === 'active' ? 'Actif' : item.status}
                            </Text>
                        </View>
                    </View>
                </View>
            </View>

            {item.current_period_end && (
                <View className="flex-row items-center mb-3">
                    <Calendar size={14} color="#64748b" />
                    <Text className="text-slate-400 text-sm ml-2">
                        Fin de période : {formatDate(item.current_period_end)}
                    </Text>
                </View>
            )}

            {item.status === 'active' && (
                <TouchableOpacity
                    onPress={() => handleCancel(item)}
                    className="bg-red-500/10 border border-red-500/30 rounded-xl py-3 items-center"
                >
                    <Text className="text-red-500 font-bold">Annuler l'abonnement</Text>
                </TouchableOpacity>
            )}
        </View>
    );

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            {/* Header */}
            <View className="flex-row items-center px-4 py-3 border-b border-slate-800">
                <TouchableOpacity onPress={() => router.back()} className="mr-3 p-1">
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>
                <Text className="text-white font-bold text-xl">Mes abonnements</Text>
            </View>

            {isLoading ? (
                <View className="flex-1 justify-center items-center">
                    <ActivityIndicator size="large" color="#10b981" />
                </View>
            ) : (
                <FlatList
                    data={subscriptions}
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
                            <CreditCard size={48} color="#475569" />
                            <Text className="text-slate-400 text-center mt-4 text-lg font-medium">
                                Aucun abonnement actif
                            </Text>
                            <Text className="text-slate-500 text-center mt-2 text-sm">
                                Abonnez-vous à un tipster pour voir ses analyses premium.
                            </Text>
                        </View>
                    }
                />
            )}
        </SafeAreaView>
    );
}

import React, { useCallback } from 'react';
import { View, FlatList, ActivityIndicator, Text, TouchableOpacity, Image, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { api } from '../../src/services/api';
import { useAuth } from '../../src/context/AuthContext';
import { Bell, Heart, MessageCircle, UserPlus, Trophy } from 'lucide-react-native';
import { showSuccessToast } from '../../src/services/toast';

// ── Types ────────────────────────────────────────────────────
interface Notification {
    id: string;
    notification_type: 'NEW_FOLLOWER' | 'NEW_LIKE' | 'NEW_COMMENT' | 'PREDICTION_RESOLVED';
    sender_username?: string;
    sender_avatar_url?: string;
    body: string;
    is_read: boolean;
    created_at: string;
}

interface PaginatedNotifications {
    results: Notification[];
    next: string | null;
    count: number;
}

// ── API calls ────────────────────────────────────────────────
const fetchNotifications = async (): Promise<PaginatedNotifications> => {
    const { data } = await api.get('/api/me/notifications/');
    return data;
};

const markAllRead = async () => {
    const { data } = await api.post('/api/me/notifications/read/');
    return data;
};

// ── Helpers ──────────────────────────────────────────────────
const getTimeAgo = (dateString: string): string => {
    const now = new Date();
    const date = new Date(dateString);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'à l\'instant';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}min`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}j`;
    return `${Math.floor(days / 7)}sem`;
};

const getNotificationIcon = (type: string) => {
    switch (type) {
        case 'NEW_FOLLOWER':
            return <UserPlus size={20} color="#10b981" />;
        case 'NEW_LIKE':
            return <Heart size={20} color="#ef4444" />;
        case 'NEW_COMMENT':
            return <MessageCircle size={20} color="#3b82f6" />;
        case 'PREDICTION_RESOLVED':
            return <Trophy size={20} color="#f59e0b" />;
        default:
            return <Bell size={20} color="#64748b" />;
    }
};

const getIconBg = (type: string): string => {
    switch (type) {
        case 'NEW_FOLLOWER': return 'bg-emerald-500/20';
        case 'NEW_LIKE': return 'bg-red-500/20';
        case 'NEW_COMMENT': return 'bg-blue-500/20';
        case 'PREDICTION_RESOLVED': return 'bg-amber-500/20';
        default: return 'bg-slate-700';
    }
};

// ── Component ────────────────────────────────────────────────
export default function NotificationsScreen() {
    const { accessToken } = useAuth();
    const queryClient = useQueryClient();
    const router = useRouter();

    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['notifications'],
        queryFn: fetchNotifications,
        enabled: !!accessToken,
    });

    const markReadMutation = useMutation({
        mutationFn: markAllRead,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
            showSuccessToast('Toutes les notifications marquées comme lues');
        },
    });

    const notifications = data?.results || [];
    const hasUnread = notifications.some((n) => !n.is_read);

    const renderNotification = useCallback(({ item }: { item: Notification }) => (
        <View
            className={`flex-row items-center px-4 py-3 border-b border-slate-800 ${!item.is_read ? 'bg-slate-900/80' : ''}`}
        >
            {/* Icon */}
            <View className={`w-10 h-10 rounded-full items-center justify-center mr-3 ${getIconBg(item.notification_type)}`}>
                {getNotificationIcon(item.notification_type)}
            </View>

            {/* Avatar */}
            {item.sender_avatar_url ? (
                <Image
                    source={{ uri: item.sender_avatar_url }}
                    className="w-10 h-10 rounded-full bg-slate-700 mr-3"
                />
            ) : item.sender_username ? (
                <View className="w-10 h-10 rounded-full bg-slate-700 mr-3 items-center justify-center">
                    <Text className="text-white font-bold text-sm">{item.sender_username[0]?.toUpperCase()}</Text>
                </View>
            ) : null}

            {/* Content */}
            <View className="flex-1">
                <Text className="text-white text-sm" numberOfLines={2}>
                    {item.sender_username && (
                        <Text className="font-bold">{item.sender_username} </Text>
                    )}
                    {item.body}
                </Text>
                <Text className="text-slate-500 text-xs mt-1">{getTimeAgo(item.created_at)}</Text>
            </View>

            {/* Unread dot */}
            {!item.is_read && (
                <View className="w-2.5 h-2.5 rounded-full bg-emerald-500 ml-2" />
            )}
        </View>
    ), []);

    // Loading
    if (isLoading) {
        return (
            <View className="flex-1 bg-slate-950 justify-center items-center">
                <ActivityIndicator size="large" color="#10b981" />
            </View>
        );
    }

    // Error
    if (error) {
        return (
            <View className="flex-1 bg-slate-950 justify-center items-center p-6">
                <Text className="text-white text-lg font-bold mb-2">Erreur</Text>
                <Text className="text-slate-400 text-center mb-6">Impossible de charger les notifications.</Text>
                <TouchableOpacity onPress={() => refetch()} className="bg-emerald-500 px-6 py-3 rounded-full">
                    <Text className="text-white font-bold">Réessayer</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            {/* Header */}
            <View className="flex-row items-center justify-between px-4 py-3 border-b border-slate-800">
                <Text className="text-white font-bold text-xl">Notifications</Text>
                {hasUnread && (
                    <TouchableOpacity
                        onPress={() => markReadMutation.mutate()}
                        disabled={markReadMutation.isPending}
                        className="bg-slate-800 px-3 py-1.5 rounded-full"
                    >
                        <Text className="text-emerald-500 font-semibold text-sm">
                            {markReadMutation.isPending ? '...' : 'Tout lire'}
                        </Text>
                    </TouchableOpacity>
                )}
            </View>

            {/* List */}
            <FlatList
                data={notifications}
                keyExtractor={(item) => item.id.toString()}
                renderItem={renderNotification}
                refreshControl={
                    <RefreshControl
                        refreshing={isLoading}
                        onRefresh={refetch}
                        tintColor="#10b981"
                    />
                }
                ListEmptyComponent={
                    <View className="flex-1 justify-center items-center p-12 mt-24">
                        <Bell size={48} color="#334155" />
                        <Text className="text-slate-500 text-center text-lg mt-4">Aucune notification</Text>
                        <Text className="text-slate-600 text-center text-sm mt-1">
                            Tu recevras des notifications quand quelqu'un te suit, aime ou commente tes paris.
                        </Text>
                    </View>
                }
                contentContainerStyle={{ paddingBottom: 100 }}
            />
        </SafeAreaView>
    );
}

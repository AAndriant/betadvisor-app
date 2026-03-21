import React from 'react';
import { View, FlatList, ActivityIndicator, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ProfileHeader } from '../../src/components/ProfileHeader';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { fetchUserProfile, fetchUserBets } from '../../src/services/users';
import { toggleFollow } from '../../src/services/social';
import { fetchMyProfile, getMySubscriptions } from '../../src/services/api';
import { showSuccessToast } from '../../src/services/toast';

interface SportStat {
    sport: string;
    total_bets: number;
    wins: number;
    winrate: number;
    roi: number;
}

const SPORT_EMOJIS: Record<string, string> = {
    Football: '⚽',
    Basketball: '🏀',
    Tennis: '🎾',
    Baseball: '⚾',
    Hockey: '🏒',
    Rugby: '🏉',
    Volleyball: '🏐',
    Handball: '🤾',
    'American Football': '🏈',
};

export default function UserProfileScreen() {
    const { id } = useLocalSearchParams<{ id: string }>();
    const router = useRouter();
    const queryClient = useQueryClient();

    // Fetch current user to determine if viewing own profile
    const { data: currentUser } = useQuery({
        queryKey: ['myProfile'],
        queryFn: fetchMyProfile,
    });

    // Fetch subscriptions to see if we are already subscribed
    const { data: mySubscriptions } = useQuery({
        queryKey: ['mySubscriptions'],
        queryFn: getMySubscriptions,
    });

    // Fetch user profile
    const { data: userProfile, isLoading: isLoadingProfile, error: profileError } = useQuery({
        queryKey: ['user', id],
        queryFn: () => fetchUserProfile(id!),
        enabled: !!id,
    });

    // Fetch user's bets
    const { data: userBets, isLoading: isLoadingBets, error: betsError } = useQuery({
        queryKey: ['userBets', id],
        queryFn: () => fetchUserBets(id!),
        enabled: !!id,
    });

    // Follow/Unfollow mutation with optimistic updates
    const followMutation = useMutation<any, Error, void>({
        mutationFn: () => toggleFollow(id!),
        onMutate: async () => {
            // Cancel outgoing refetches
            await queryClient.cancelQueries({ queryKey: ['user', id] });

            // Snapshot the previous value
            const previousProfile = queryClient.getQueryData(['user', id]);

            // Optimistically update
            queryClient.setQueryData(['user', id], (old: any) => {
                if (!old) return old;
                return {
                    ...old,
                    is_followed_by_me: !old.is_followed_by_me,
                    follower_count: old.is_followed_by_me
                        ? old.follower_count - 1
                        : old.follower_count + 1,
                };
            });

            return { previousProfile };
        },
        onError: (_err: any, _variables: any, context: any) => {
            // Revert on error
            if (context?.previousProfile) {
                queryClient.setQueryData(['user', id], context.previousProfile);
            }
        },
        onSettled: () => {
            // Show toast feedback
            const profile: any = queryClient.getQueryData(['user', id]);
            if (profile?.is_followed_by_me) {
                showSuccessToast(`Tu suis ${profile.username}`);
            } else {
                showSuccessToast('Abonné retiré');
            }
            // Refetch to ensure consistency
            queryClient.invalidateQueries({ queryKey: ['user', id] });
        },
    });

    const handleToggleFollow = () => {
        followMutation.mutate();
    };

    const handleNavigateToComments = (betId: string) => {
        router.push({
            pathname: '/comments/[id]',
            params: { id: betId }
        });
    };

    const handleSubscribe = () => {
        router.push({
            pathname: '/subscribe',
            params: { tipsterId: id }
        });
    };

    const isOwnProfile = currentUser?.id === id;
    const isSubscribed = Array.isArray(mySubscriptions)
        ? mySubscriptions.some((sub: any) => String(sub.tipster) === String(id))
        : false;

    // Loading state
    if (isLoadingProfile) {
        return (
            <View className="flex-1 bg-slate-950 justify-center items-center">
                <ActivityIndicator size="large" color="#10b981" />
                <Text className="text-slate-500 mt-4">Chargement du profil...</Text>
            </View>
        );
    }

    // Error state
    if (profileError || !userProfile) {
        return (
            <View className="flex-1 bg-slate-950 justify-center items-center p-6">
                <Text className="text-white text-lg font-bold mb-2">Erreur</Text>
                <Text className="text-slate-400 text-center">
                    Impossible de charger le profil de cet utilisateur.
                </Text>
            </View>
        );
    }

    // Format user data for ProfileHeader
    const formattedUser = {
        name: userProfile.username,
        handle: userProfile.username,
        role: userProfile.is_tipster ? ('TIPSTER' as const) : ('PUNTER' as const),
        isVerified: true,
        avatarUrl: userProfile.avatar_url,
        bio: userProfile.bio || '',
        stats: {
            roi: userProfile.stats?.roi || 0,
            winRate: userProfile.stats?.win_rate || 0,
            followers: userProfile.follower_count || 0,
        },
        haloColor: userProfile.halo_color || 'none',
    };

    // S10-08: Sport stats
    const sportStats: SportStat[] = (userProfile as any).sport_stats || [];

    // Empty state component
    const EmptyState = () => (
        <View className="flex-1 justify-center items-center p-8 mt-12">
            <Text className="text-slate-400 text-center text-lg">
                Ce Tipster n'a pas encore publié de paris
            </Text>
        </View>
    );

    // ✅ FIX: Gérer la réponse paginée du backend { results: [...] }
    const betsList = Array.isArray(userBets) ? userBets : (userBets?.results || []);

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            <FlatList
                data={betsList}
                keyExtractor={(item: any) => item.id.toString()}
                ListHeaderComponent={
                    <>
                        <ProfileHeader
                            user={formattedUser}
                            isFollowed={userProfile.is_followed_by_me}
                            onToggleFollow={handleToggleFollow}
                            isOwnProfile={isOwnProfile}
                            isSubscribed={isSubscribed}
                            onSubscribe={handleSubscribe}
                        />

                        {/* S10-08: Stats par sport */}
                        {sportStats.length > 0 && (
                            <View className="px-4 mt-4">
                                <Text className="text-white font-bold text-lg mb-3">Stats par sport</Text>
                                <View className="flex-row flex-wrap">
                                    {sportStats.map((stat) => (
                                        <View
                                            key={stat.sport}
                                            className="bg-slate-900 rounded-xl p-3 mr-2 mb-2 border border-slate-800"
                                        >
                                            <Text className="text-white font-bold text-sm">
                                                {SPORT_EMOJIS[stat.sport] || '🏅'} {stat.sport}
                                            </Text>
                                            <Text className="text-slate-400 text-xs mt-1">
                                                {stat.winrate}% WR · {stat.roi > 0 ? '+' : ''}{stat.roi}% ROI
                                            </Text>
                                        </View>
                                    ))}
                                </View>
                            </View>
                        )}
                    </>
                }
                renderItem={({ item }) => (
                    <View className="px-4 py-2">
                        <TicketCard
                            title={item.match_title}
                            odds={parseFloat(item.odds) || 0}
                            status={item.status}
                            roi={item.roi || null}
                            id={item.id.toString()}
                            likeCount={item.like_count || 0}
                            commentCount={item.comment_count || 0}
                            isLiked={item.is_liked_by_me || false}
                            onPressComment={() => handleNavigateToComments(item.id.toString())}
                            isLocked={item.is_locked || false}
                            onUnlock={handleSubscribe}
                        />
                    </View>
                )}
                ListEmptyComponent={isLoadingBets ? null : <EmptyState />}
                contentContainerStyle={{ paddingBottom: 100 }}
            />
            {isLoadingBets && (
                <View className="py-4">
                    <ActivityIndicator size="small" color="#10b981" />
                </View>
            )}
        </SafeAreaView>
    );
}

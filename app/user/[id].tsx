import React from 'react';
import { View, FlatList, ActivityIndicator, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ProfileHeader } from '../../src/components/ProfileHeader';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { fetchUserProfile, fetchUserBets } from '../../src/services/users';
import { toggleFollow } from '../../src/services/social';
import { fetchMyProfile } from '../../src/services/api';

export default function UserProfileScreen() {
    const { id } = useLocalSearchParams<{ id: string }>();
    const router = useRouter();
    const queryClient = useQueryClient();

    // Fetch current user to determine if viewing own profile
    const { data: currentUser } = useQuery({
        queryKey: ['myProfile'],
        queryFn: fetchMyProfile,
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
    const followMutation = useMutation({
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
        onError: (err, variables, context) => {
            // Revert on error
            if (context?.previousProfile) {
                queryClient.setQueryData(['user', id], context.previousProfile);
            }
        },
        onSettled: () => {
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

    const isOwnProfile = currentUser?.id === id;

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
        role: 'TIPSTER' as const,
        isVerified: true,
        avatarUrl: userProfile.avatar_url,
        stats: {
            roi: userProfile.stats?.roi || 0,
            winRate: userProfile.stats?.win_rate || 0,
            followers: userProfile.follower_count || 0,
        },
    };

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
                    <ProfileHeader
                        user={formattedUser}
                        isFollowed={userProfile.is_followed_by_me}
                        onToggleFollow={handleToggleFollow}
                        isOwnProfile={isOwnProfile}
                    />
                }
                renderItem={({ item }) => (
                    <View className="px-4 py-2">
                        <TicketCard
                            title={item.match_title}
                            odds={parseFloat(item.odds)}
                            status={item.status}
                            roi={item.roi || null}
                            id={item.id.toString()}
                            likeCount={item.like_count || 0}
                            commentCount={item.comment_count || 0}
                            isLiked={item.is_liked_by_me || false}
                            onPressComment={() => handleNavigateToComments(item.id.toString())}
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

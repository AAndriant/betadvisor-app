import React, { useState, useCallback } from 'react';
import { View, FlatList, ActivityIndicator, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { useAuth } from '../../src/context/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../src/services/api';

interface PaginatedBets {
  results: any[];
  next: string | null;
  previous: string | null;
  count: number;
}

export default function FeedScreen() {
  const { accessToken } = useAuth();
  const router = useRouter();
  const [allBets, setAllBets] = useState<any[]>([]);
  const [nextPage, setNextPage] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);

  const { isLoading, error, refetch } = useQuery({
    queryKey: ['feed'],
    queryFn: async () => {
      const { data } = await api.get('/api/bets/');
      const paginated = data as PaginatedBets;
      const list = paginated.results || (Array.isArray(data) ? data : []);
      setAllBets(list);
      setNextPage(paginated.next || null);
      return data;
    },
    enabled: !!accessToken,
  });

  const handleNavigateToComments = (betId: string) => {
    router.push({
      pathname: '/comments/[id]',
      params: { id: betId }
    });
  };

  const handleLoadMore = useCallback(async () => {
    if (!nextPage || loadingMore) return;

    setLoadingMore(true);
    try {
      const { data } = await api.get(nextPage);
      const paginated = data as PaginatedBets;
      const newResults = paginated.results || [];
      setAllBets((prev) => [...prev, ...newResults]);
      setNextPage(paginated.next || null);
    } catch (e) {
      console.error('Error loading more bets:', e);
    } finally {
      setLoadingMore(false);
    }
  }, [nextPage, loadingMore]);

  const handleRefresh = useCallback(() => {
    setAllBets([]);
    setNextPage(null);
    refetch();
  }, [refetch]);

  if (isLoading && allBets.length === 0) return <View className="flex-1 bg-slate-950 justify-center"><ActivityIndicator size="large" color="#10b981" /></View>;

  if (error) return (
    <View className="flex-1 bg-slate-950 justify-center items-center">
      <Text className="text-white">Erreur de chargement</Text>
    </View>
  );

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      <View className="px-4 py-2 border-b border-slate-800">
        <Text className="text-white font-bold text-xl">Flux Récent</Text>
      </View>

      <FlatList
        data={allBets}
        keyExtractor={(item: any) => item.id.toString()}
        renderItem={({ item }) => (
          <View className="px-4 py-2">
            <TicketCard
              title={item.match_title}
              odds={parseFloat(item.odds)}
              status={item.status}
              roi={null}
              id={item.id.toString()}
              likeCount={item.like_count || 0}
              commentCount={item.comment_count || 0}
              isLiked={item.is_liked_by_me || false}
              onPressComment={() => handleNavigateToComments(item.id.toString())}
              authorId={item.author_id}
              authorName={item.author_name}
              authorAvatar={item.author_avatar}
              onPressAuthor={() => router.push({
                pathname: '/user/[id]',
                params: { id: item.author_id }
              })}
            />
          </View>
        )}
        onRefresh={handleRefresh}
        refreshing={isLoading}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.3}
        ListFooterComponent={loadingMore ? (
          <View className="py-4">
            <ActivityIndicator size="small" color="#10b981" />
          </View>
        ) : null}
        contentContainerStyle={{ paddingBottom: 100 }}
      />
    </SafeAreaView>
  );
}

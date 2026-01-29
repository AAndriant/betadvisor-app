import React from 'react';
import { View, FlatList, ActivityIndicator, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { useFeed } from '../../src/hooks/useBets';

export default function FeedScreen() {
  const { data: bets, isLoading, error, refetch } = useFeed();
  const router = useRouter();

  const handleNavigateToComments = (betId: string) => {
    router.push({
      pathname: '/comments/[id]',
      params: { id: betId }
    });
  };

  if (isLoading) return <View className="flex-1 bg-slate-950 justify-center"><ActivityIndicator size="large" color="#10b981" /></View>;

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
        data={bets}
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
            />
            <Text className="text-slate-500 text-xs mt-1 ml-2">Par {item.author_name}</Text>
          </View>
        )}
        onRefresh={refetch}
        refreshing={isLoading}
        contentContainerStyle={{ paddingBottom: 100 }}
      />
    </SafeAreaView>
  );
}

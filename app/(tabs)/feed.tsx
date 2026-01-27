import React, { useCallback } from 'react';
import { View, Text, FlatList, ActivityIndicator, RefreshControl } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { getTickets } from '../../src/services/api';
import { TicketCard } from '../../src/components/TicketCard';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function FeedScreen() {
  const { data, isLoading, isError, error, refetch, isRefetching } = useQuery({
    queryKey: ['tickets', 'list'],
    queryFn: () => getTickets(),
  });

  const onRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  if (isLoading) {
    return (
      <View className="flex-1 justify-center items-center bg-gray-50">
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  if (isError) {
    return (
      <View className="flex-1 justify-center items-center bg-gray-50 p-4">
        <Text className="text-red-500 text-center mb-4">Une erreur est survenue lors du chargement du feed.</Text>
        <Text className="text-gray-500 text-center mb-4">{(error as Error).message}</Text>
      </View>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-gray-50" edges={['top']}>
      <FlatList
        data={data?.results}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => <TicketCard ticket={item} />}
        contentContainerStyle={{ paddingVertical: 16 }}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={onRefresh} colors={['#3b82f6']} />
        }
        ListEmptyComponent={
            <View className="flex-1 justify-center items-center mt-20">
                <Text className="text-gray-500">Aucun ticket pour le moment.</Text>
            </View>
        }
      />
    </SafeAreaView>
  );
}

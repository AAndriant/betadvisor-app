import React, { useState } from 'react';
import { View, ScrollView, Text, TouchableOpacity, ActivityIndicator, RefreshControl, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ProfileHeader } from '../../src/components/ProfileHeader';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { useUserStats } from '../../src/hooks/useUserStats';
import { fetchUserBets } from '../../src/services/users';

export default function ProfileScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('Bets');

  // 1. Appel API via le Hook
  const { data: user, isLoading, error, refetch } = useUserStats();

  // 2. Fetch real bets for this user
  const { data: userBets, isLoading: isLoadingBets, refetch: refetchBets } = useQuery({
    queryKey: ['myBets', user?.id],
    queryFn: () => fetchUserBets(user!.id),
    enabled: !!user?.id,
  });

  const handleNavigateToComments = (betId: string) => {
    router.push({
      pathname: '/comments/[id]',
      params: { id: betId }
    });
  };

  // 2. Gestion Loading
  if (isLoading) {
    return (
      <View className="flex-1 bg-slate-950 justify-center items-center">
        <ActivityIndicator size="large" color="#10b981" />
        <Text className="text-slate-500 mt-4">Chargement du profil...</Text>
      </View>
    );
  }

  // 3. Gestion Erreur (Backend éteint ou erreur réseau)
  if (error || !user) {
    return (
      <View className="flex-1 bg-slate-950 justify-center items-center p-6">
        <Text className="text-white text-lg font-bold mb-2">Erreur de connexion</Text>
        <Text className="text-slate-400 text-center mb-6">Impossible de joindre le serveur. Vérifie que le Backend (Django) tourne bien sur le port 8000.</Text>
        <TouchableOpacity
          onPress={() => refetch()}
          className="bg-emerald-500 px-6 py-3 rounded-full"
        >
          <Text className="text-white font-bold">Réessayer</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // 4. Adaptateur de données (API -> UI)
  const formattedUser = {
    name: user.username || "Utilisateur",
    handle: user.username,
    role: user.is_tipster ? ('TIPSTER' as const) : ('PUNTER' as const),
    isVerified: true,
    avatarUrl: user.avatar_url,
    bio: user.bio || '',
    stats: {
      roi: user.stats?.roi || 0,
      winRate: user.stats?.win_rate || 0,
      followers: user.follower_count || 0
    }
  };

  // Parse paginated response
  const betsList = Array.isArray(userBets) ? userBets : (userBets?.results || []);

  return (
    <SafeAreaView className="flex-1 bg-slate-950 pb-24">
      <FlatList
        data={activeTab === 'Bets' ? betsList : []}
        keyExtractor={(item: any) => item.id.toString()}
        ListHeaderComponent={
          <>
            {/* Header connecté à l'API */}
            <ProfileHeader user={formattedUser} isOwnProfile={true} />

            {/* Bouton Devenir Tipster (uniquement pour les non-tipsters) */}
            {!user.is_tipster && (
              <View className="px-4 mt-4">
                <TouchableOpacity
                  onPress={() => router.push('/tipster-onboarding')}
                  className="bg-emerald-500 py-3 rounded-xl items-center"
                >
                  <Text className="text-white font-bold text-lg">Devenir Tipster</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Tabs Statiques */}
            <View className="flex-row border-b border-slate-800 px-4 mt-2">
              {['Bets', 'Stats', 'Media'].map((tab) => (
                <TouchableOpacity
                  key={tab}
                  onPress={() => setActiveTab(tab)}
                  className={`mr-6 pb-3 ${activeTab === tab ? 'border-b-2 border-emerald-500' : ''}`}
                >
                  <Text className={`font-medium ${activeTab === tab ? 'text-white' : 'text-slate-500'}`}>
                    {tab}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </>
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
        ListEmptyComponent={
          activeTab === 'Bets' ? (
            isLoadingBets ? (
              <View className="py-12 items-center">
                <ActivityIndicator size="small" color="#10b981" />
              </View>
            ) : (
              <View className="py-12 items-center">
                <Text className="text-slate-500 text-center text-base">Aucun pari publié</Text>
                <Text className="text-slate-600 text-center text-sm mt-1">Tes paris apparaîtront ici une fois publiés.</Text>
              </View>
            )
          ) : (
            <View className="py-12 items-center">
              <Text className="text-slate-500 text-center text-base">Bientôt disponible</Text>
            </View>
          )
        }
        refreshControl={
          <RefreshControl
            refreshing={isLoading}
            onRefresh={() => { refetch(); refetchBets(); }}
            tintColor="#10b981"
          />
        }
        contentContainerStyle={{ paddingBottom: 100 }}
      />
    </SafeAreaView>
  );
}

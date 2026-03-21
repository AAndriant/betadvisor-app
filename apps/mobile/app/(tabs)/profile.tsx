import React, { useState } from 'react';
import { View, ScrollView, Text, TouchableOpacity, ActivityIndicator, RefreshControl, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ProfileHeader } from '../../src/components/ProfileHeader';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { useUserStats } from '../../src/hooks/useUserStats';
import { fetchUserBets } from '../../src/services/users';
import { settleBet, getTipsterStatus, TipsterStatus } from '../../src/services/api';
import { showSuccessToast } from '../../src/services/toast';

interface SportStat {
  sport: string;
  total_bets: number;
  wins: number;
  winrate: number;
  roi: number;
}

interface Badge {
  badge_name: string;
  description: string;
  awarded_at: string;
}

const BADGE_EMOJIS: Record<string, string> = {
  'First Win': '🏆',
  'Hot Streak 3': '🔥',
  'Hot Streak 5': '💎',
  'Hot Streak 10': '👑',
  'Century Club': '💯',
  'Sharp Shooter': '🎯',
  'ROI King': '📈',
};

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

export default function ProfileScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('Bets');

  // 1. Appel API via le Hook
  const { data: user, isLoading, error, refetch } = useUserStats();

  // 2. Fetch real bets for this user
  const { data: userBets, isLoading: isLoadingBets, refetch: refetchBets } = useQuery({
    queryKey: ['myBets', user?.id],
    queryFn: () => fetchUserBets(user!.id),
    enabled: !!user?.id,
  });

  // 3. Fetch tipster/onboarding status for CTA logic
  const { data: tipsterStatus, refetch: refetchTipsterStatus } = useQuery<TipsterStatus>({
    queryKey: ['tipsterStatus'],
    queryFn: getTipsterStatus,
    enabled: !!user?.id,
  });

  const handleNavigateToComments = (betId: string) => {
    router.push({
      pathname: '/comments/[id]',
      params: { id: betId }
    });
  };

  // S10-03: Handle settle
  const handleSettle = async (betId: string, outcome: 'WON' | 'LOST' | 'VOID') => {
    try {
      await settleBet(betId, outcome);
      showSuccessToast(`Pari résolu : ${outcome}`);
      queryClient.invalidateQueries({ queryKey: ['myBets'] });
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
    } catch {
      // Error toast handled by interceptor
    }
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
    },
    haloColor: user.halo_color || 'none',
  };

  // Parse paginated response
  const betsList = Array.isArray(userBets) ? userBets : (userBets?.results || []);

  // S10-08: Sport stats
  const sportStats: SportStat[] = user.sport_stats || [];

  return (
    <SafeAreaView className="flex-1 bg-slate-950 pb-24">
      <FlatList
        data={activeTab === 'Bets' ? betsList : []}
        keyExtractor={(item: any) => item.id.toString()}
        ListHeaderComponent={
          <>
            {/* Header connecté à l'API */}
            <ProfileHeader user={formattedUser} isOwnProfile={true} />

            {/* S10-10A: Tipster CTA — 3 states */}
            {(() => {
              const isTipster = user.is_tipster || tipsterStatus?.is_tipster;
              const isFullyOnboarded = tipsterStatus?.onboarding_completed && tipsterStatus?.charges_enabled;

              if (!isTipster) {
                // State 1: Not a tipster yet
                return (
                  <View className="px-4 mt-4">
                    <TouchableOpacity
                      onPress={() => router.push('/tipster-onboarding')}
                      className="bg-emerald-500 rounded-xl py-4 items-center"
                    >
                      <Text className="text-white font-bold text-lg">🚀 Devenir Tipster</Text>
                      <Text className="text-emerald-100 text-xs mt-1">Monétise tes pronostics</Text>
                    </TouchableOpacity>
                  </View>
                );
              }

              if (isTipster && !isFullyOnboarded) {
                // State 2: Tipster but Stripe onboarding incomplete
                return (
                  <View className="px-4 mt-4">
                    <TouchableOpacity
                      onPress={() => router.push('/tipster-onboarding')}
                      className="bg-amber-500/20 border border-amber-500 rounded-xl py-4 items-center"
                    >
                      <Text className="text-amber-400 font-bold text-lg">⚠️ Finaliser l'onboarding Stripe</Text>
                      <Text className="text-amber-300/70 text-xs mt-1">Complète ta vérification pour recevoir des paiements</Text>
                    </TouchableOpacity>
                  </View>
                );
              }

              // State 3: Fully onboarded tipster
              return (
                <View className="px-4 mt-4">
                  <TouchableOpacity
                    onPress={() => router.push('/(tabs)/dashboard')}
                    className="bg-slate-900 border border-emerald-500 rounded-xl py-3 items-center"
                  >
                    <Text className="text-emerald-500 font-bold text-lg">📊 Mon Dashboard</Text>
                  </TouchableOpacity>
                </View>
              );
            })()}

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

            {/* P2-14: Badges */}
            {user.badges && user.badges.length > 0 && (
              <View className="px-4 mt-4">
                <Text className="text-white font-bold text-lg mb-3">Badges</Text>
                <View className="flex-row flex-wrap">
                  {user.badges.map((badge: Badge) => (
                    <View
                      key={badge.badge_name}
                      className="bg-slate-900 rounded-xl px-3 py-2 mr-2 mb-2 border border-amber-500/30 flex-row items-center"
                    >
                      <Text className="text-lg mr-1.5">
                        {BADGE_EMOJIS[badge.badge_name] || '🏅'}
                      </Text>
                      <Text className="text-amber-400 font-semibold text-xs">
                        {badge.badge_name}
                      </Text>
                    </View>
                  ))}
                </View>
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
              odds={parseFloat(item.odds) || 0}
              status={item.status}
              roi={item.roi || null}
              id={item.id.toString()}
              likeCount={item.like_count || 0}
              commentCount={item.comment_count || 0}
              isLiked={item.is_liked_by_me || false}
              onPressComment={() => handleNavigateToComments(item.id.toString())}
              isOwner={true}
              onSettle={(outcome) => handleSettle(item.id.toString(), outcome)}
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
            onRefresh={() => { refetch(); refetchBets(); refetchTipsterStatus(); }}
            tintColor="#10b981"
          />
        }
        contentContainerStyle={{ paddingBottom: 100 }}
      />
    </SafeAreaView>
  );
}

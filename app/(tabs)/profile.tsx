import React, { useState } from 'react';
import { View, ScrollView, Text, TouchableOpacity, ActivityIndicator, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ProfileHeader } from '../../src/components/ProfileHeader';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { LockedContentOverlay } from '../../src/components/LockedContentOverlay';
import { useUserStats } from '../../src/hooks/useUserStats';

// Mock temporaire pour les tickets (le backend endpoint tickets viendra après)
const MOCK_TICKETS = [
  { id: '1', match: 'PSG vs OM', odds: 1.85, stake: 100, status: 'WIN', date: '2h ago', isPremium: false },
  { id: '2', match: 'Lakers vs Bulls', odds: 2.10, stake: 100, status: 'PENDING', date: '5h ago', isPremium: true },
];

export default function ProfileScreen() {
  const [activeTab, setActiveTab] = useState('Bets');

  // 1. Appel API via le Hook
  const { data: user, isLoading, error, refetch } = useUserStats();
  const isSubscriber = false;

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
  // On sécurise les données au cas où l'API renvoie des nulls
  const formattedUser = {
    name: user.username || "Utilisateur",
    handle: user.username,
    role: 'TIPSTER' as const, // Forcé pour démo
    isVerified: true,
    avatarUrl: user.avatar_url,
    stats: {
      roi: user.stats?.roi || 0,
      winRate: user.stats?.win_rate || 0,
      followers: user.stats?.total_bets || 0
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-slate-950 pb-24">
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#10b981" />
        }
      >

        {/* Header connecté à l'API */}
        <ProfileHeader user={formattedUser} isOwnProfile={true} />

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

        {/* Liste des Tickets (Reste Mockée pour l'instant) */}
        <View className="p-4 gap-4">
          {MOCK_TICKETS.map((ticket) => (
            <View key={ticket.id} className="relative">
              <TicketCard
                title={ticket.match}
                odds={ticket.odds}
                status={ticket.status as any}
                roi={null}
              />
              {ticket.isPremium && !isSubscriber && (
                <LockedContentOverlay onUnlock={() => console.log('Open Paywall')} />
              )}
            </View>
          ))}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

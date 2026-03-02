import React, { useState } from 'react';
import { View, ScrollView, Text, TouchableOpacity, ActivityIndicator, RefreshControl, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import { useQuery } from '@tanstack/react-query';
import { ProfileHeader } from '../../src/components/ProfileHeader';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { LockedContentOverlay } from '../../src/components/LockedContentOverlay';
import { useUserStats } from '../../src/hooks/useUserStats';
import { createConnectAccount, getOnboardingLink, getConnectStatus } from '../../src/services/api';

// Mock temporaire pour les tickets (le backend endpoint tickets viendra après)
const MOCK_TICKETS = [
  { id: '1', match: 'PSG vs OM', odds: 1.85, stake: 100, status: 'WIN', date: '2h ago', isPremium: false },
  { id: '2', match: 'Lakers vs Bulls', odds: 2.10, stake: 100, status: 'PENDING', date: '5h ago', isPremium: true },
];

export default function ProfileScreen() {
  const [activeTab, setActiveTab] = useState('Bets');
  const [isConnectingStripe, setIsConnectingStripe] = useState(false);

  // 1. Appel API via le Hook
  const { data: user, isLoading, error, refetch: refetchUser } = useUserStats();
  const isSubscriber = false;

  const { data: stripeStatus, refetch: refetchStripeStatus } = useQuery({
    queryKey: ['stripeStatus'],
    queryFn: getConnectStatus,
  });

  const handleRefetch = () => {
    refetchUser();
    refetchStripeStatus();
  };

  const handleStripeConnect = async () => {
    setIsConnectingStripe(true);
    try {
      const returnUrl = Linking.createURL('stripe-return', { scheme: 'betadvisor' });
      const refreshUrl = Linking.createURL('stripe-refresh', { scheme: 'betadvisor' });

      let linkResponse;
      try {
        linkResponse = await getOnboardingLink(returnUrl, refreshUrl);
      } catch (err: any) {
        if (err.response?.status === 404) {
          await createConnectAccount();
          linkResponse = await getOnboardingLink(returnUrl, refreshUrl);
        } else {
          throw err;
        }
      }

      const result = await WebBrowser.openAuthSessionAsync(linkResponse.url, returnUrl);
      if (result.type === 'success' || result.type === 'dismiss' || result.type === 'cancel') {
        await refetchStripeStatus();
      }
    } catch (error) {
      console.error('Stripe Connect error:', error);
      Alert.alert('Erreur', 'Impossible de démarrer l\'onboarding Stripe.');
    } finally {
      setIsConnectingStripe(false);
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
          onPress={() => handleRefetch()}
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
          <RefreshControl refreshing={isLoading} onRefresh={handleRefetch} tintColor="#10b981" />
        }
      >

        {/* Header connecté à l'API */}
        <ProfileHeader user={formattedUser} isOwnProfile={true} />

        {/* Stripe Connect CTA (for Tipsters only) */}
        {formattedUser.role === 'TIPSTER' && (
          <View className="px-4 mt-4">
            {!stripeStatus?.exists || !stripeStatus?.onboarding_completed ? (
              <TouchableOpacity
                onPress={handleStripeConnect}
                disabled={isConnectingStripe}
                className={`bg-indigo-600 rounded-xl p-4 items-center ${isConnectingStripe ? 'opacity-50' : ''}`}
              >
                {isConnectingStripe ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text className="text-white font-bold text-base">
                    Connecter Stripe
                  </Text>
                )}
                {stripeStatus?.exists && !stripeStatus?.onboarding_completed && !isConnectingStripe && (
                  <Text className="text-indigo-200 text-xs mt-1">
                    Onboarding en attente, appuyez pour terminer.
                  </Text>
                )}
              </TouchableOpacity>
            ) : (
              <View className="bg-emerald-900/30 border border-emerald-800 rounded-xl p-4 flex-row justify-between items-center">
                <View>
                  <Text className="text-emerald-400 font-bold text-base">
                    Stripe Connecté
                  </Text>
                  {stripeStatus?.charges_enabled ? (
                    <Text className="text-emerald-200/70 text-xs mt-1">
                      Vous pouvez recevoir des paiements
                    </Text>
                  ) : (
                    <Text className="text-yellow-400/70 text-xs mt-1">
                      En attente de vérification finale
                    </Text>
                  )}
                </View>
              </View>
            )}
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

        {/* Liste des Tickets (Reste Mockée pour l'instant) */}
        <View className="p-4 gap-4">
          {MOCK_TICKETS.map((ticket) => (
            <View key={ticket.id} className="relative">
              <TicketCard
                title={ticket.match}
                odds={ticket.odds}
                status={ticket.status as any}
                roi={null}
                id={ticket.id}
                likeCount={0}
                commentCount={0}
                isLiked={false}
                onPressComment={() => {}}
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

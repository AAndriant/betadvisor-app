import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, Text, TouchableOpacity, Alert } from 'react-native';
import { WebView, WebViewNavigation } from 'react-native-webview';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQueryClient } from '@tanstack/react-query';
import { becomeTipster, BecomeTipsterResponse } from '../src/services/api';
import { showSuccessToast } from '../src/services/toast';

export default function TipsterOnboardingScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const startOnboarding = async () => {
    try {
      setLoading(true);
      setError(null);

      const response: BecomeTipsterResponse = await becomeTipster();

      if (response.status === 'already_onboarded') {
        // Already fully onboarded — redirect to dashboard
        showSuccessToast(response.message || 'Vous êtes déjà tipster !');
        queryClient.invalidateQueries({ queryKey: ['myProfile'] });
        router.replace('/(tabs)/dashboard');
        return;
      }

      if (response.status === 'onboarding_required' && response.onboarding_url) {
        setUrl(response.onboarding_url);
      } else {
        setError('Aucun lien d\'onboarding reçu.');
      }
    } catch (err: any) {
      console.error('Error in become-tipster flow:', err);
      const serverMsg = err.response?.data?.error;
      setError(serverMsg || 'Impossible de lancer l\'onboarding Stripe.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    startOnboarding();
  }, []);

  const handleNavigationStateChange = (navState: WebViewNavigation) => {
    const currentUrl = navState.url;

    if (currentUrl.includes('/api/connect/return/')) {
      // Successfully completed onboarding (or returned from it)
      showSuccessToast('Onboarding terminé ! 🎉');
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      queryClient.invalidateQueries({ queryKey: ['tipsterStatus'] });
      router.replace('/(tabs)/dashboard');
    } else if (currentUrl.includes('/api/connect/refresh/')) {
      // Session expired or needs refresh, fetch a new link
      setUrl(null);
      startOnboarding();
    }
  };

  if (loading) {
    return (
      <View className="flex-1 bg-slate-950 justify-center items-center">
        <ActivityIndicator size="large" color="#10b981" />
        <Text className="text-slate-500 mt-4">Création de votre profil tipster...</Text>
        <Text className="text-slate-600 text-sm mt-2">Connexion à Stripe Connect...</Text>
      </View>
    );
  }

  if (error || !url) {
    return (
      <View className="flex-1 bg-slate-950 justify-center items-center p-6">
        <Text className="text-white text-lg font-bold mb-2">Erreur</Text>
        <Text className="text-slate-400 text-center mb-6">{error || 'Erreur inconnue'}</Text>
        <TouchableOpacity
          onPress={() => router.back()}
          className="bg-slate-800 px-6 py-3 rounded-full mb-4"
        >
          <Text className="text-white font-bold">Retour</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={startOnboarding}
          className="bg-emerald-500 px-6 py-3 rounded-full"
        >
          <Text className="text-white font-bold">Réessayer</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      {/* Header */}
      <View className="px-4 py-3 border-b border-slate-800 flex-row items-center justify-between">
        <TouchableOpacity onPress={() => {
          Alert.alert(
            'Quitter l\'onboarding ?',
            'Vous pourrez reprendre plus tard depuis votre profil.',
            [
              { text: 'Continuer', style: 'cancel' },
              { text: 'Quitter', style: 'destructive', onPress: () => {
                queryClient.invalidateQueries({ queryKey: ['myProfile'] });
                router.back();
              }},
            ]
          );
        }}>
          <Text className="text-slate-400 text-base">✕ Fermer</Text>
        </TouchableOpacity>
        <Text className="text-white font-bold text-base">Stripe Connect</Text>
        <View style={{ width: 70 }} />
      </View>

      <WebView
        source={{ uri: url }}
        onNavigationStateChange={handleNavigationStateChange}
        startInLoadingState={true}
        renderLoading={() => (
          <View className="absolute inset-0 bg-slate-950 justify-center items-center">
            <ActivityIndicator size="large" color="#10b981" />
          </View>
        )}
      />
    </SafeAreaView>
  );
}

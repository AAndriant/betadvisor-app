import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, Text, TouchableOpacity } from 'react-native';
import { WebView, WebViewNavigation } from 'react-native-webview';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Linking from 'expo-linking';
import { useQueryClient } from '@tanstack/react-query';
import { createSubscriptionCheckout } from '../src/services/api';
import { showSuccessToast } from '../src/services/toast';

export default function SubscribeScreen() {
  const router = useRouter();
  const { tipsterId } = useLocalSearchParams<{ tipsterId: string }>();
  const queryClient = useQueryClient();

  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCheckoutUrl = async () => {
    if (!tipsterId) {
      setError("Aucun tipster spécifié.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Create proper deep links so that external banking apps can redirect back into our app/webview
      const successUrl = Linking.createURL('/return/success');
      const cancelUrl = Linking.createURL('/return/cancel');

      const response = await createSubscriptionCheckout(tipsterId, successUrl, cancelUrl);

      if (response && response.checkout_url) {
        setUrl(response.checkout_url);
      } else {
        setError('Aucun lien de paiement reçu.');
      }
    } catch (err: any) {
      console.error('Error fetching checkout url:', err);
      setError('Impossible de générer le lien de paiement.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCheckoutUrl();
  }, [tipsterId]);

  const handleNavigationStateChange = (navState: WebViewNavigation) => {
    const currentUrl = navState.url;

    if (currentUrl.includes('/return/success')) {
      // Invalidate queries so that subscriptions and profile are refreshed
      queryClient.invalidateQueries({ queryKey: ['mySubscriptions'] });
      showSuccessToast('Abonnement souscrit avec succès !');
      // Go back to the tipster profile
      router.back();
    } else if (currentUrl.includes('/return/cancel')) {
      // Payment cancelled, just go back
      router.back();
    }
  };

  if (loading) {
    return (
      <View className="flex-1 bg-slate-950 justify-center items-center">
        <ActivityIndicator size="large" color="#10b981" />
        <Text className="text-slate-500 mt-4">Préparation du paiement...</Text>
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
          onPress={fetchCheckoutUrl}
          className="bg-emerald-500 px-6 py-3 rounded-full"
        >
          <Text className="text-white font-bold">Réessayer</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
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

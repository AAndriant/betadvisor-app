import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, Text, TouchableOpacity } from 'react-native';
import { WebView, WebViewNavigation } from 'react-native-webview';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createConnectedAccount, getOnboardingLink } from '../src/services/api';

export default function TipsterOnboardingScreen() {
  const router = useRouter();
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLink = async () => {
    try {
      setLoading(true);
      setError(null);
      // Try to create the account first. If the user already has one, the API should return a 400.
      // We catch the error and proceed to get the onboarding link.
      try {
        await createConnectedAccount();
      } catch (err: any) {
        if (err.response && err.response.status === 400) {
          console.log('User might already have a ConnectedAccount, proceeding to get onboarding link');
        } else {
          throw err;
        }
      }

      const response = await getOnboardingLink();
      if (response && response.url) {
        setUrl(response.url);
      } else {
        setError('No onboarding link received.');
      }
    } catch (err: any) {
      console.error('Error fetching onboarding link:', err);
      setError('Impossible de générer le lien Stripe.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLink();
  }, []);

  const handleNavigationStateChange = (navState: WebViewNavigation) => {
    const currentUrl = navState.url;

    // The backend uses request.build_absolute_uri('/api/connect/return/') and '/api/connect/refresh/'
    if (currentUrl.includes('/api/connect/return/')) {
      // Successfully completed onboarding (or returned from it)
      router.replace('/(tabs)/profile');
    } else if (currentUrl.includes('/api/connect/refresh/')) {
      // Session expired or needs refresh, fetch a new link
      setUrl(null);
      fetchLink();
    }
  };

  if (loading) {
    return (
      <View className="flex-1 bg-slate-950 justify-center items-center">
        <ActivityIndicator size="large" color="#10b981" />
        <Text className="text-slate-500 mt-4">Chargement de Stripe Connect...</Text>
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
          onPress={fetchLink}
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

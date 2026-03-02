import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, StyleSheet, Alert, Text, TouchableOpacity } from 'react-native';
import { WebView, WebViewNavigation } from 'react-native-webview';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as Linking from 'expo-linking';
import { createSubscriptionCheckout } from '../src/services/api';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft } from 'lucide-react-native';

export default function SubscribeScreen() {
  const { tipster_id } = useLocalSearchParams<{ tipster_id: string }>();
  const router = useRouter();
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function initCheckout() {
      if (!tipster_id) {
        setError("L'ID du tipster est manquant.");
        setLoading(false);
        return;
      }

      try {
        const successUrl = Linking.createURL('/feed', { queryParams: { status: 'success' } });
        const cancelUrl = Linking.createURL('/feed', { queryParams: { status: 'cancelled' } });

        const response = await createSubscriptionCheckout(tipster_id, successUrl, cancelUrl);
        if (response.checkout_url) {
          setCheckoutUrl(response.checkout_url);
        } else {
          setError("Impossible de récupérer l'URL de paiement.");
        }
      } catch (err: any) {
        console.error("Erreur Checkout:", err);
        setError(err.response?.data?.error || "Une erreur est survenue lors de l'initialisation du paiement.");
      } finally {
        setLoading(false);
      }
    }

    initCheckout();
  }, [tipster_id]);

  const handleNavigationStateChange = (navState: WebViewNavigation) => {
    const { url } = navState;
    if (url.includes('status=success')) {
      Alert.alert('Succès', 'Votre abonnement a été activé !');
      router.replace('/(tabs)/feed');
    } else if (url.includes('status=cancelled')) {
      Alert.alert('Annulé', 'Le paiement a été annulé.');
      router.back();
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#10b981" />
      </View>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <ArrowLeft color="white" size={24} />
          </TouchableOpacity>
        </View>
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={() => router.back()} style={styles.button}>
            <Text style={styles.buttonText}>Retour</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (checkoutUrl) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <ArrowLeft color="white" size={24} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Paiement Sécurisé</Text>
        </View>
        <WebView
          source={{ uri: checkoutUrl }}
          onNavigationStateChange={handleNavigationStateChange}
          style={styles.webview}
          startInLoadingState={true}
          renderLoading={() => (
            <View style={styles.webviewLoading}>
              <ActivityIndicator size="large" color="#10b981" />
            </View>
          )}
        />
      </SafeAreaView>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#020617', // slate-950
  },
  center: {
    flex: 1,
    backgroundColor: '#020617',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  webview: {
    flex: 1,
  },
  webviewLoading: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#020617',
  },
  errorText: {
    color: '#f87171', // red-400
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b', // slate-800
  },
  backButton: {
    marginRight: 16,
  },
  headerTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  button: {
    backgroundColor: '#10b981', // emerald-500
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  buttonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  }
});
